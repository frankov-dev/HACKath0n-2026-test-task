import os
import django

# Налаштовуємо Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings') # Перевір, чи твій проєкт називається 'core'
django.setup()

from django.contrib.auth.models import User
from api.models import DeliveryPoint, EmployeeProfile, ResourceType, Stock, Supplier, Warehouse

def seed_data():
    print("Наповнення бази даними...")

    # 1. Очищення старих даних (опціонально, щоб не дублювати)
    EmployeeProfile.objects.all().delete()
    User.objects.filter(username__in=['dispatcher_admin', 'manager_kyiv_point', 'manager_lviv_warehouse']).delete()
    Supplier.objects.all().delete()
    Warehouse.objects.all().delete()
    DeliveryPoint.objects.all().delete()

    # 2. Дані для постачальників
    suppliers_data = [
        {"name": "ТОВ Нафтотрейд", "city": "Київ", "latitude": 50.4510, "longitude": 30.5200},
        {"name": "Логістика Захід", "city": "Львів", "latitude": 49.8390, "longitude": 24.0300},
    ]
    supplier_by_city = {}
    for supplier in suppliers_data:
        obj = Supplier.objects.create(**supplier)
        supplier_by_city[obj.city] = obj
        print(f"Створено постачальника: {obj.name}")

    # 3. Дані для Складів (Хаби)
    warehouses_data = [
        {"name": "Київський Центральний Хаб", "city": "Київ", "latitude": 50.4501, "longitude": 30.5234},
        {"name": "Західний Логістичний Центр", "city": "Львів", "latitude": 49.8397, "longitude": 24.0297},
        {"name": "Південний Морський Хаб", "city": "Одеса", "latitude": 46.4825, "longitude": 30.7233},
        {"name": "Подільський Резерв", "city": "Хмельницький", "latitude": 49.4230, "longitude": 26.9871},
    ]

    created_warehouses = {}
    for wh in warehouses_data:
        supplier = supplier_by_city.get(wh['city'])
        if supplier is None:
            supplier = supplier_by_city.get('Київ')
        obj = Warehouse.objects.create(**wh, supplier=supplier)
        created_warehouses[wh['name']] = obj
        # Додаємо запаси на кожен склад
        Stock.objects.create(warehouse=obj, resource_type=ResourceType.FUEL, actual_quantity=5000.0)
        Stock.objects.create(warehouse=obj, resource_type=ResourceType.GOODS, actual_quantity=2000.0)
        print(f"Створено склад: {wh['name']}")

    # 4. Дані для Точок (Магазини / АЗС)
    points_data = [
        {"name": "АЗС №1", "city": "Київ", "latitude": 50.4000, "longitude": 30.6000},
        {"name": "Магазин 'Продукти'", "city": "Хмельницький", "latitude": 49.4300, "longitude": 27.0000},
        {"name": "АЗС №12", "city": "Львів", "latitude": 49.8000, "longitude": 24.0000},
        {"name": "ТЦ 'Захід'", "city": "Ужгород", "latitude": 48.6208, "longitude": 22.2879},
        {"name": "Портовий Маркет", "city": "Одеса", "latitude": 46.4700, "longitude": 30.7400},
    ]

    created_points = {}
    for pt in points_data:
        obj = DeliveryPoint.objects.create(**pt)
        created_points[pt['name']] = obj
        print(f"Створено точку: {pt['name']}")

    # 5. Тестові користувачі з ролями
    dispatcher = User.objects.create_user(
        username='dispatcher_admin',
        password='Dispatcher123!'
    )
    dispatcher.is_staff = True
    dispatcher.is_superuser = True
    dispatcher.save(update_fields=['is_staff', 'is_superuser'])
    EmployeeProfile.objects.create(user=dispatcher, role=EmployeeProfile.Role.DISPATCHER)

    kyiv_point_manager = User.objects.create_user(
        username='manager_kyiv_point',
        password='PointManager123!'
    )
    EmployeeProfile.objects.create(
        user=kyiv_point_manager,
        role=EmployeeProfile.Role.DELIVERY_POINT_MANAGER,
        delivery_point=created_points['АЗС №1'],
    )

    lviv_warehouse_manager = User.objects.create_user(
        username='manager_lviv_warehouse',
        password='WarehouseManager123!'
    )
    EmployeeProfile.objects.create(
        user=lviv_warehouse_manager,
        role=EmployeeProfile.Role.WAREHOUSE_MANAGER,
        warehouse=created_warehouses['Західний Логістичний Центр'],
    )

    print("\nСтворено тестових користувачів:")
    print("- dispatcher_admin / Dispatcher123!")
    print("- manager_kyiv_point / PointManager123!")
    print("- manager_lviv_warehouse / WarehouseManager123!")

    print("\nБазу успішно наповнено! Тепер API не порожнє.")

if __name__ == "__main__":
    seed_data()