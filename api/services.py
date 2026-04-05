from django.db import transaction
from .models import AllocationHistory, PriorityLevel, Request, RequestStatus, ResourceTransaction, Stock, TransactionType
from .utils import calculate_distance

class LogisticsService:
    @staticmethod
    def recalculate_resource(resource_type):
        """Повний перерахунок алокацій для конкретного ресурсу (urgent-first)."""
        with transaction.atomic():
            stocks = (
                Stock.objects.select_for_update()
                .filter(resource_type=resource_type)
            )
            for stock in stocks:
                stock.reserved_quantity = 0.0
                stock.save(update_fields=['reserved_quantity'])

            requests = list(
                Request.objects.select_for_update()
                .filter(resource_type=resource_type)
                .exclude(status=RequestStatus.CANCELLED)
                .order_by('-is_urgent', '-priority', 'created_at', 'id')
            )

            for req in requests:
                req.quantity_allocated = 0.0
                req.status = RequestStatus.PENDING
                req.save(update_fields=['quantity_allocated', 'status'])

            ResourceTransaction.objects.filter(resource_type=resource_type).delete()

            for req in requests:
                LogisticsService.process_request(req)

    @staticmethod
    def process_request(request_instance):
        """Головний конвеєр обробки запиту."""
        with transaction.atomic():
            # Працюємо з оновленою версією заявки в межах транзакції.
            request_instance = Request.objects.select_for_update().get(pk=request_instance.pk)

            # 1. Спочатку пробуємо знайти вільне на складах
            LogisticsService._allocate_from_free_stocks(request_instance)

            # 2. Якщо запит критичний і все ще не закритий, забираємо ресурс у нижчих пріоритетів.
            if (
                request_instance.priority == PriorityLevel.CRITICAL
                and request_instance.quantity_allocated < request_instance.quantity_requested
            ):
                LogisticsService._preempt_low_priority(request_instance)

            # 3. Оновлюємо фінальний статус
            request_instance.update_status()
            request_instance.save()

            shortage_quantity = request_instance.quantity_requested - request_instance.quantity_allocated
            if shortage_quantity > 0:
                ResourceTransaction.objects.create(
                    request=request_instance,
                    resource_type=request_instance.resource_type,
                    transaction_type=TransactionType.SHORTAGE,
                    quantity=shortage_quantity,
                    from_location='Система розподілу',
                    to_location=f"Точка: {request_instance.point.name}",
                    note='Недостатньо ресурсу для повного покриття запиту',
                )

    @staticmethod
    def _allocate_from_free_stocks(req):
        """Шукаємо вільні ресурси на найближчих складах."""
        stocks = (
            Stock.objects.select_for_update()
            .select_related('warehouse')
            .filter(resource_type=req.resource_type, actual_quantity__gt=0)
        )
        
        # Сортуємо склади за відстанню до точки
        stocks_with_dist = []
        for s in stocks:
            d = calculate_distance(req.point.latitude, req.point.longitude, s.warehouse.latitude, s.warehouse.longitude)
            stocks_with_dist.append((d, s))
        stocks_with_dist.sort(key=lambda x: x[0])

        for dist, stock in stocks_with_dist:
            needed = req.quantity_requested - req.quantity_allocated
            if needed <= 0: break
            
            can_take = min(needed, stock.available_quantity)
            if can_take > 0:
                stock.reserved_quantity += can_take
                stock.save()
                req.quantity_allocated += can_take
                ResourceTransaction.objects.create(
                    request=req,
                    resource_type=req.resource_type,
                    transaction_type=TransactionType.ALLOCATION,
                    quantity=can_take,
                    from_location=f"Склад: {stock.warehouse.name}",
                    to_location=f"Точка: {req.point.name}",
                    note=f'Виділено з найближчого доступного складу ({dist:.1f} км)',
                )

    @staticmethod
    def _preempt_low_priority(critical_req):
        """Перерозподіляємо вже виділену кількість від менш пріоритетних заявок."""
        needed = critical_req.quantity_requested - critical_req.quantity_allocated

        donors = (
            Request.objects.select_for_update()
            .filter(
                resource_type=critical_req.resource_type,
                priority__lt=PriorityLevel.CRITICAL,
                quantity_allocated__gt=0,
            )
            .order_by('priority', 'created_at')
        )

        for donor in donors:
            if needed <= 0:
                break

            transferred = min(donor.quantity_allocated, needed)
            if transferred <= 0:
                continue

            donor_old_quantity = donor.quantity_allocated
            critical_old_quantity = critical_req.quantity_allocated

            donor.quantity_allocated -= transferred
            donor.update_status()
            donor.save()

            ResourceTransaction.objects.create(
                request=donor,
                resource_type=donor.resource_type,
                transaction_type=TransactionType.PREEMPT_OUT,
                quantity=transferred,
                from_location=f"Точка: {donor.point.name}",
                to_location=f"Точка: {critical_req.point.name}",
                note='Списано на користь критичного запиту',
            )

            critical_req.quantity_allocated += transferred
            critical_req.update_status()

            ResourceTransaction.objects.create(
                request=critical_req,
                resource_type=critical_req.resource_type,
                transaction_type=TransactionType.PREEMPT_IN,
                quantity=transferred,
                from_location=f"Точка: {donor.point.name}",
                to_location=f"Точка: {critical_req.point.name}",
                note='Отримано через перерозподіл від нижчого пріоритету',
            )

            AllocationHistory.objects.create(
                request=donor,
                old_quantity=donor_old_quantity,
                new_quantity=donor.quantity_allocated,
                reason='Перерозподіл ресурсу на користь критичного запиту',
            )
            AllocationHistory.objects.create(
                request=critical_req,
                old_quantity=critical_old_quantity,
                new_quantity=critical_req.quantity_allocated,
                reason='Отримано ресурс шляхом перерозподілу від нижчого пріоритету',
            )

            needed -= transferred
