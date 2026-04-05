# from .models import Stock

# def handle_resource_allocation(request_instance):
#     """
#     Ця функція шукає товар на складах і бронює його.
#     """
#     # 1. Знаходимо всі склади, де є цей тип ресурсу (напр. ПАЛИВО)
#     # Сортуємо так, щоб спочатку брати з найбільших залишків
#     stocks = Stock.objects.filter(
#         resource_type=request_instance.resource_type,
#         actual_quantity__gt=0
#     ).order_by('-actual_quantity')

#     needed = request_instance.quantity_requested
#     allocated_total = 0

#     for stock in stocks:
#         if needed <= 0:
#             break
        
#         # Скільки реально вільного товару на цьому складі?
#         available = stock.available_quantity # Наша property з моделей
        
#         if available > 0:
#             # Беремо або скільки треба, або скільки є
#             to_take = min(needed, available)
            
#             # Оновлюємо склад (резервуємо)
#             stock.reserved_quantity += to_take
#             stock.save()

#             allocated_total += to_take
#             needed -= to_take

#     # 2. Оновлюємо сам запит
#     request_instance.quantity_allocated = allocated_total
    
#     if allocated_total >= request_instance.quantity_requested:
#         request_instance.status = 'ALLOCATED' # Повністю розподілено
#     elif allocated_total > 0:
#         request_instance.status = 'PARTIAL'   # Частково
#     else:
#         request_instance.status = 'PENDING'   # Товар не знайдено, в черзі
        
#     request_instance.save()