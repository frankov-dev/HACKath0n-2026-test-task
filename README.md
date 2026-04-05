# Logistics Hub API + Frontend

Проєкт Logistics Hub реалізує прикладну систему розподілу ресурсів між складами та точками доставки. Робота виконана в межах тестового завдання для відбору на хакатон.

## 1. Призначення системи

Система забезпечує:
- прийом і обробку заявок на ресурси (`FUEL`, `GOODS`, `SUPPLIES`);
- автоматизований розподіл ресурсів зі складів з урахуванням пріоритету та терміновості;
- перерозподіл на користь критичних заявок у разі дефіциту;
- ведення журналу транзакцій (`ALLOCATION`, `PREEMPT_OUT`, `PREEMPT_IN`, `SHORTAGE`);
- рольову модель доступу (RBAC) та ізоляцію даних між користувачами.

## 2. Технологічний стек

Backend:
- Python, Django 6, Django REST Framework;
- Token Authentication (`rest_framework.authtoken`);
- drf-spectacular (OpenAPI / Swagger);
- SQLite.

Frontend:
- React 19 + Vite;
- Tailwind CSS.

## 3. Структура репозиторію

- `core/` - конфігурація Django та головна маршрутизація;
- `api/` - доменні моделі, API-шар, сервіси, тести;
- `frontend/` - клієнтський інтерфейс;
- `seed_db.py` - скрипт підготовки демо-даних;
- `db.sqlite3` - локальна база даних.

## 4. Запуск проєкту

### 4.1 Backend

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python seed_db.py
python manage.py runserver
```

Сервіс буде доступний за адресою:
- `http://127.0.0.1:8000/`;
- API префікс: `http://127.0.0.1:8000/api/`.

### 4.2 Frontend

```powershell
cd frontend
npm install
npm run dev
```

Клієнтський застосунок за замовчуванням доступний за адресою:
- `http://127.0.0.1:5173/`.

### 4.3 Запуск через Docker Compose

Вимоги:
- встановлені Docker Desktop та Docker Compose.

Запуск backend + frontend однією командою (з кореня проєкту):

```powershell
docker compose up --build
```

Після запуску сервіси доступні за адресами:
- Backend: `http://127.0.0.1:8000/`;
- Frontend: `http://127.0.0.1:5173/`.

За потреби створити демо-дані всередині контейнера backend:

```powershell
docker compose exec backend python seed_db.py
```

Або запустити із автоматичним seed під час старту:

```powershell
docker compose run -e SEED_DB=1 --service-ports backend
```

Зупинка та видалення контейнерів:

```powershell
docker compose down
```

## 5. Демо-облікові записи

Після виконання `python seed_db.py` створюються тестові користувачі:
- Dispatcher: `dispatcher_admin` / `Dispatcher123!`;
- Delivery Point Manager: `manager_kyiv_point` / `PointManager123!`;
- Warehouse Manager: `manager_lviv_warehouse` / `WarehouseManager123!`.

## 6. Авторизація

### 6.1 Вхід у систему

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

Для доступу до захищених ендпоінтів необхідно передавати:

```http
Authorization: Token <token>
```

### 6.2 Режим доступу до службових маршрутів API

- `GET /api/` (API Root) є публічним і доступний без авторизації; маршрут виконує роль навігаційної точки та повертає перелік команд.
- `GET /api/docs/` (Swagger UI) доступний лише для авторизованих користувачів.
- `GET /api/schema/` (OpenAPI schema) доступний лише для авторизованих користувачів.

Таким чином, публічним є лише вхідний API Root, а документація та схема захищені механізмами автентифікації.

## 7. Ролі та права доступу (RBAC)

### 7.1 DISPATCHER
- повний доступ до заявок;
- перегляд усіх складів, точок, постачальників і транзакцій.

### 7.2 DELIVERY_POINT_MANAGER
- перегляд лише власної точки та пов'язаних заявок;
- створення, редагування та видалення заявок у межах своєї зони відповідальності;
- поле `point` під час створення/оновлення заявки примусово прив'язується до точки менеджера.

### 7.3 WAREHOUSE_MANAGER
- перегляд свого складу та відповідних постачальників;
- перегляд заявок і транзакцій;
- відсутність прав на зміну заявок.

## 8. Основні API ендпоінти

Базовий префікс: `/api/`.

Службові:
- `GET /api/`;
- `GET /api/me/` або `GET /api/auth/me/`;
- `POST /api/auth/login/`;
- `POST /api/auth/logout/`.

Каталоги:
- `GET /api/warehouses/`;
- `GET /api/warehouses/{id}/`;
- `GET /api/warehouses/nearest/?resource_type=FUEL&latitude=50.45&longitude=30.52&limit=10`;
- `GET /api/suppliers/`;
- `GET /api/suppliers/{id}/`;
- `GET /api/points/`;
- `GET /api/points/{id}/`.

Заявки:
- `GET /api/requests/`;
- `POST /api/requests/`;
- `GET /api/requests/{id}/`;
- `PATCH /api/requests/{id}/`;
- `DELETE /api/requests/{id}/`.

Журнал руху ресурсів:
- `GET /api/transactions/`;
- `GET /api/transactions/{id}/`.

Фільтри для `/api/transactions/`:
- `?resource_type=FUEL|GOODS|SUPPLIES`;
- `?request=<request_id>`;
- `?transaction_type=ALLOCATION|PREEMPT_OUT|PREEMPT_IN|SHORTAGE`.

Документація:
- `GET /api/schema/` (authentication required);
- `GET /api/docs/` (authentication required).

## 9. Ключові доменні моделі

- `Supplier` - постачальник ресурсів;
- `Warehouse` - складський вузол;
- `Stock` - залишки ресурсу на складі (`actual_quantity`, `reserved_quantity`, `available_quantity`);
- `DeliveryPoint` - точка доставки;
- `EmployeeProfile` - профіль ролі та прив'язка користувача;
- `Request` - заявка на ресурс;
- `ResourceTransaction` - журнал руху ресурсу;
- `AllocationHistory` - історія змін алокації;
- `Shipment` - модель відправлення.

## 10. Принцип роботи алгоритму розподілу

Після створення, оновлення або видалення заявки виконується перерахунок для відповідного типу ресурсу:
1. обнулення резервів для ресурсу;
2. впорядкування заявок за правилом `is_urgent DESC`, `priority DESC`, `created_at ASC`;
3. алокація з найближчих складів за географічною дистанцією;
4. у випадку критичних заявок - перерозподіл з заявок нижчого пріоритету;
5. при неповному покритті - фіксація `SHORTAGE` транзакції.

## 11. Тестування

Smoke-перевірка API:

```powershell
python manage.py smoke_api
```

Набір unit/API тестів:

```powershell
python manage.py test api
```

## 12. Додаткові відомості

- у проєкті реалізовано ізоляцію даних на рівні queryset та permissions;
- OpenAPI-специфікація генерується автоматично через drf-spectacular;
- документація API (`/api/docs/`, `/api/schema/`) свідомо захищена авторизацією;
- параметри `DEBUG=True` і `CORS_ALLOW_ALL_ORIGINS=True` застосовані виключно для локального тестового середовища.

