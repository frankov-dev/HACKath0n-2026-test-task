# Logistics Hub API + Frontend

Тестове завдання для відбору на хакатон: система розподілу ресурсів між складами та точками доставки.

## Що робить проєкт

Система дозволяє:
- створювати та обробляти заявки на ресурси (`FUEL`, `GOODS`, `SUPPLIES`);
- автоматично розподіляти ресурси зі складів за пріоритетом і терміновістю;
- виконувати перерозподіл на користь критичних заявок;
- вести журнал транзакцій (`ALLOCATION`, `PREEMPT_OUT`, `PREEMPT_IN`, `SHORTAGE`);
- обмежувати доступ до даних за ролями (RBAC).

## Технологічний стек

Backend:
- Python, Django 6, Django REST Framework
- Token Authentication (`rest_framework.authtoken`)
- drf-spectacular (OpenAPI / Swagger)
- SQLite

Frontend:
- React 19 + Vite
- Tailwind CSS

## Структура проєкту

- `core/` - Django налаштування та головні URL
- `api/` - моделі, серіалізатори, в'юхи, бізнес-логіка, тести
- `frontend/` - React клієнт
- `seed_db.py` - наповнення БД демо-даними
- `db.sqlite3` - локальна база даних

## Швидкий запуск (локально)

### 1. Backend

1. Перейти в корінь проєкту.
2. Створити та активувати віртуальне оточення.
3. Встановити залежності.
4. Виконати міграції.
5. Заповнити демо-дані.
6. Запустити сервер.

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python seed_db.py
python manage.py runserver
```

Backend буде доступний на:
- `http://127.0.0.1:8000/`
- API root: `http://127.0.0.1:8000/api/`

### 2. Frontend

У новому терміналі:

```powershell
cd frontend
npm install
npm run dev
```

Frontend за замовчуванням стартує на:
- `http://127.0.0.1:5173/`

## Демо-користувачі

Після `python seed_db.py` доступні акаунти:

- Dispatcher: `dispatcher_admin` / `Dispatcher123!`
- Delivery point manager: `manager_kyiv_point` / `PointManager123!`
- Warehouse manager: `manager_lviv_warehouse` / `WarehouseManager123!`

## Авторизація

### Login

`POST /api/auth/login/`

Body:

```json
{
  "username": "dispatcher_admin",
  "password": "Dispatcher123!"
}
```

Response:

```json
{
  "token": "<token>",
  "user": {
    "id": 1,
    "username": "dispatcher_admin",
    "role": "DISPATCHER",
    "delivery_point_id": null,
    "warehouse_id": null
  }
}
```

Для захищених ендпоінтів передавайте заголовок:

```http
Authorization: Token <token>
```

## Ролі та доступ (RBAC)

### DISPATCHER
- повний доступ до заявок;
- бачить всі склади, точки, постачальників, транзакції.

### DELIVERY_POINT_MANAGER
- бачить тільки власну точку та заявки своєї точки;
- може створювати/редагувати/видаляти заявки;
- `point` при створенні/оновленні заявки примусово прив'язується до його точки.

### WAREHOUSE_MANAGER
- бачить свій склад та пов'язаних постачальників;
- бачить список заявок і транзакцій;
- не має прав на створення/редагування/видалення заявок.

## Основні API ендпоінти

Базовий префікс: `/api/`

### Службові
- `GET /api/` - API root (підказка доступних команд)
- `GET /api/me/` або `GET /api/auth/me/` - поточний користувач
- `POST /api/auth/login/` - отримати token
- `POST /api/auth/logout/` - logout (видаляє token)

### Каталоги
- `GET /api/warehouses/`
- `GET /api/warehouses/{id}/`
- `GET /api/warehouses/nearest/?resource_type=FUEL&latitude=50.45&longitude=30.52&limit=10`
- `GET /api/suppliers/`
- `GET /api/suppliers/{id}/`
- `GET /api/points/`
- `GET /api/points/{id}/`

### Заявки
- `GET /api/requests/`
- `POST /api/requests/`
- `GET /api/requests/{id}/`
- `PATCH /api/requests/{id}/`
- `DELETE /api/requests/{id}/`

### Журнал руху ресурсів
- `GET /api/transactions/`
- `GET /api/transactions/{id}/`

Фільтри для `/api/transactions/`:
- `?resource_type=FUEL|GOODS|SUPPLIES`
- `?request=<request_id>`
- `?transaction_type=ALLOCATION|PREEMPT_OUT|PREEMPT_IN|SHORTAGE`

### Документація API
- `GET /api/schema/`
- `GET /api/docs/`

Примітка: `/api/schema/` і `/api/docs/` захищені авторизацією.

## Ключові моделі домену

- `Supplier` - постачальник ресурсу.
- `Warehouse` - склад (може бути прив'язаний до постачальника).
- `Stock` - залишки ресурсу на складі (`actual_quantity`, `reserved_quantity`, `available_quantity`).
- `DeliveryPoint` - точка доставки (магазин/АЗС).
- `EmployeeProfile` - роль користувача + прив'язка до точки або складу.
- `Request` - заявка на ресурс (пріоритет, терміновість, статус, виділена кількість).
- `ResourceTransaction` - журнал операцій розподілу/перерозподілу/нестачі.
- `AllocationHistory` - історія змін алокації під час перерозподілу.
- `Shipment` - модель відправлення (підготовлена в домені).

## Логіка розподілу (коротко)

При створенні/оновленні/видаленні заявки запускається перерахунок по типу ресурсу:
1. Скидання резервів для цього ресурсу.
2. Сортування заявок за правилом: `is_urgent DESC`, `priority DESC`, `created_at ASC`.
3. Алокація з найближчих складів (за дистанцією).
4. Для критичних заявок - перерозподіл з lower-priority заявок.
5. Якщо ресурсу не вистачило - фіксується `SHORTAGE` транзакція.

## Перевірка якості та демо

### Автоматичний smoke-тест API

```powershell
python manage.py smoke_api
```

Що перевіряє команда:
- логін кожної ролі;
- доступ до ключових endpoint-ів;
- рольові обмеження (ізоляція даних);
- сценарій критичного перерозподілу.

### Запуск unit/API тестів

```powershell
python manage.py test api
```

## Типовий сценарій демо (2-3 хв)

1. Логін під `dispatcher_admin`.
2. Показати список заявок, складів та транзакцій.
3. Створити критичну заявку.
4. Показати в журналі `PREEMPT_OUT` / `PREEMPT_IN` / `SHORTAGE` (якщо виникне нестача).
5. Перелогінитись під `manager_kyiv_point` і показати, що видно лише свою точку/заявки.

## Важливі зауваження

- Налаштування `CORS_ALLOW_ALL_ORIGINS = True` увімкнене для локальної розробки.
- `DEBUG=True` та SQLite використані для тестового середовища.
- Для production потрібно винести секрети в env-змінні і посилити security налаштування.

---

Якщо потрібно, можу додати англомовну версію README або окремий блок "Architecture Decision Notes" для технічного інтерв'ю.