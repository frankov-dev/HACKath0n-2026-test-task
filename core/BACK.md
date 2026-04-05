# Backend Contract for Frontend

Цей файл — практичний гайд для фронтенду: що є в бекенді, як це викликати і яку поведінку очікувати.

## 1. Що вже реалізовано

- Token Authentication для всіх API-запитів (окрім логіну).
- Рольова модель користувача:
  - `DISPATCHER`
  - `DELIVERY_POINT_MANAGER`
  - `WAREHOUSE_MANAGER`
- Ізоляція даних по ролях для заявок.
- Автоприв'язка заявки менеджера точки до його `DeliveryPoint`.
- Логістичний алгоритм розподілу:
  - пошук найближчих складів,
  - облік резервів,
  - перерозподіл для критичних заявок,
  - лог транзакцій руху ресурсу.

## 2. Швидкий старт

1. Міграції:

```bash
python manage.py migrate
```

2. Сід демо-даних:

```bash
python seed_db.py
```

3. Запуск:

```bash
python manage.py runserver
```

## 3. Авторизація

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

### Поточний користувач

`GET /api/auth/me/`

Header для всіх захищених endpoint-ів:

```http
Authorization: Token <token>
```

## 4. Демо-користувачі

Після `seed_db.py`:

- `dispatcher_admin` / `Dispatcher123!`
- `manager_kyiv_point` / `PointManager123!`
- `manager_lviv_warehouse` / `WarehouseManager123!`

## 5. API для фронтенду

База: `/api/`

### Каталоги

- `GET /api/warehouses/`
- `GET /api/warehouses/{id}/`
- `GET /api/warehouses/nearest/?resource_type=FUEL&latitude=50.45&longitude=30.52&limit=10`
- `GET /api/suppliers/`
- `GET /api/points/`

### Операційні

- `GET /api/requests/`
- `POST /api/requests/`
- `GET /api/requests/{id}/`
- `PUT/PATCH /api/requests/{id}/`
- `DELETE /api/requests/{id}/`

### Аудит/лог руху

- `GET /api/transactions/`
- `GET /api/transactions/{id}/`
- Фільтри:
  - `?resource_type=FUEL`
  - `?request=<id>`
  - `?transaction_type=ALLOCATION|PREEMPT_OUT|PREEMPT_IN|SHORTAGE`

### Документація API

- `GET /api/schema/`
- `GET /api/docs/`

Примітка: schema/docs теж захищені токеном.

## 6. Рольова поведінка (критично для UI)

### DISPATCHER

- Бачить всі заявки.
- Створює/редагує заявки без обмежень точки.

### DELIVERY_POINT_MANAGER

- Бачить тільки заявки своєї точки.
- При створенні/редагуванні заявки поле `point` примусово ставиться на його точку.
- Не може працювати з чужими заявками (деталь чужої заявки повертає 404).

### WAREHOUSE_MANAGER

- Бачить список заявок (зараз без додаткових обмежень).

## 7. Як працює логіка розподілу

При create/update/delete заявки викликається перерахунок по типу ресурсу:

1. Скидається `reserved_quantity` для відповідного ресурсу.
2. Заявки сортуються: urgent first -> higher priority -> earlier created.
3. Розподіл йде з найближчих складів.
4. Якщо заявка `CRITICAL` і ресурсу не вистачає:
   - забирається частина у lower-priority заявок,
   - пишуться транзакції `PREEMPT_OUT/PREEMPT_IN`.
5. Якщо покриття неповне -> `SHORTAGE`.

## 8. Що має зробити фронтенд

1. На старті показати тільки форму логіну.
2. Зберегти token (memory/localStorage) і додавати у `Authorization`.
3. Після логіну викликати `/api/auth/me/` і побудувати UI по ролі.
4. Для таблиць:
   - заявки: `/api/requests/`
   - склади: `/api/warehouses/`
   - рух ресурсів: `/api/transactions/`
5. При помилці 401 -> logout + редірект на login.

## 9. Готова перевірка перед демо

Швидкий end-to-end smoke:

```bash
python manage.py smoke_api
```

Команда:

- логіниться під кожною роллю,
- проходить основні endpoint-и,
- перевіряє рольову ізоляцію,
- перевіряє критичний перерозподіл.

Якщо є `FAIL`, команда завершується з code 1.
