from django.db import transaction
from .models import Stock, Request
from .utils import calculate_distance

class LogisticsService:
    @staticmethod
    def process_request(request_instance):
        """Головний конвеєр обробки запиту."""
        with transaction.atomic():
            # 1. Спочатку пробуємо знайти вільне на складах
            LogisticsService._allocate_from_free_stocks(request_instance)
            
            # 2. Якщо запит КРИТИЧНИЙ і все ще не заповнений — вмикаємо "Робін Гуда"
            if request_instance.priority == 3 and request_instance.quantity_allocated < request_instance.quantity_requested:
                LogisticsService._preempt_low_priority(request_instance)
            
            # 3. Оновлюємо фінальний статус
            request_instance.update_status() 
            request_instance.save()

    @staticmethod
    def _allocate_from_free_stocks(req):
        """Шукаємо вільні ресурси на найближчих складах."""
        stocks = Stock.objects.filter(resource_type=req.resource_type, actual_quantity__gt=0)
        
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

    @staticmethod
    def _preempt_low_priority(critical_req):
        """Забираємо ресурси у звичайних запитів для критичного."""
        needed = critical_req.quantity_requested - critical_req.quantity_allocated
        
        # Шукаємо "чужі" замовлення, які вже мають товар, але пріоритет нижчий (1 або 2)
        others = Request.objects.filter(
            resource_type=critical_req.resource_type,
            priority__lt=3,
            quantity_allocated__gt=0
        ).order_by('priority', '-created_at') # Спочатку найменш важливі та найновіші

        for other in others:
            if needed <= 0: break
            
            can_steal = min(other.quantity_allocated, needed)
            
            # Переписуємо літри з одного на інший
            other.quantity_allocated -= can_steal
            other.update_status()
            other.save()
            
            critical_req.quantity_allocated += can_steal
            needed -= can_steal