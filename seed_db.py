import os
import django

# Налаштовуємо Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings') # Перевір, чи твій проєкт називається 'core'
django.setup()

from api.models import Warehouse, DeliveryPoint, Stock, ResourceType

def seed_data():
    print("Наповнення бази даними...")

    # 1. Очищення старих даних (опціонально, щоб не дублювати)
    Warehouse.objects.all().delete()
    DeliveryPoint.objects.all().delete()

    # 2. Дані для Складів (Хаби)
    warehouses_data = [
        {"name": "Київський Центральний Хаб", "city": "Київ", "latitude": 50.4501, "longitude": 30.5234},
        {"name": "Західний Логістичний Центр", "city": "Львів", "latitude": 49.8397, "longitude": 24.0297},
        {"name": "Південний Морський Хаб", "city": "Одеса", "latitude": 46.4825, "longitude": 30.7233},
        {"name": "Подільський Резерв", "city": "Хмельницький", "latitude": 49.4230, "longitude": 26.9871},
    ]

    for wh in warehouses_data:
        obj = Warehouse.objects.create(**wh)
        # Додаємо запаси на кожен склад
        Stock.objects.create(warehouse=obj, resource_type=ResourceType.FUEL, actual_quantity=5000.0)
        Stock.objects.create(warehouse=obj, resource_type=ResourceType.GOODS, actual_quantity=2000.0)
        print(f"Створено склад: {wh['name']}")

    # 3. Дані для Точок (Магазини / АЗС)
    points_data = [
        {"name": "АЗС №1", "city": "Київ", "latitude": 50.4000, "longitude": 30.6000},
        {"name": "Магазин 'Продукти'", "city": "Хмельницький", "latitude": 49.4300, "longitude": 27.0000},
        {"name": "АЗС №12", "city": "Львів", "latitude": 49.8000, "longitude": 24.0000},
        {"name": "ТЦ 'Захід'", "city": "Ужгород", "latitude": 48.6208, "longitude": 22.2879},
        {"name": "Портовий Маркет", "city": "Одеса", "latitude": 46.4700, "longitude": 30.7400},
    ]

    for pt in points_data:
        DeliveryPoint.objects.create(**pt)
        print(f"Створено точку: {pt['name']}")

    print("\nБазу успішно наповнено! Тепер API не порожнє.")

if __name__ == "__main__":
    seed_data()