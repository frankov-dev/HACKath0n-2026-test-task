from django.db import transaction
from .models import Stock, Request, RequestStatus
from .utils import calculate_distance

class LogisticsService:
    @staticmethod
    def process_request(request_instance):
        """Головний конвеєр обробки запиту."""
        with transaction.atomic():
            # Працюємо з оновленою версією заявки в межах транзакції.
            request_instance = Request.objects.select_for_update().get(pk=request_instance.pk)

            # 1. Спочатку пробуємо знайти вільне на складах
            LogisticsService._allocate_from_free_stocks(request_instance)

            # 2. Оновлюємо фінальний статус
            request_instance.update_status() 
            request_instance.save()

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
