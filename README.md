# Transport Logistics Backend (Hackathon MVP)

Backend for resource distribution across warehouses, suppliers, and delivery points.

## Stack

- Django 6
- Django REST Framework
- drf-spectacular (OpenAPI + Swagger UI)
- SQLite (default)

## Run

```bash
python manage.py migrate
python manage.py runserver
```

API docs:

- `/api/schema/` - OpenAPI schema
- `/api/docs/` - Swagger UI

## Data Models

### Supplier

- `name`, `city`, `latitude`, `longitude`
- Linked to warehouses (`Warehouse.supplier`)

### Warehouse

- `name`, `city`, `latitude`, `longitude`
- Optional `supplier`

### Stock

- `warehouse`, `resource_type`
- `actual_quantity`, `reserved_quantity`
- `available_quantity = actual_quantity - reserved_quantity`

### DeliveryPoint

- `name`, `city`, `latitude`, `longitude`

### Request

- `point`, `resource_type`, `quantity_requested`
- `quantity_allocated`, `priority`, `is_urgent`, `status`
- Status lifecycle: `PENDING`, `PARTIAL`, `ALLOCATED`, `SHIPPED`, `COMPLETED`, `CANCELLED`

### ResourceTransaction

Detailed movement log for dashboard and audit:

- `transaction_type`: `ALLOCATION`, `PREEMPT_OUT`, `PREEMPT_IN`, `SHORTAGE`
- `resource_type`, `quantity`, `from_location`, `to_location`, `note`
- Optional link to `request`

## Allocation Logic

Main service: `LogisticsService`.

### 1) Resource recalculation (dynamic demand)

When request is created/updated, backend triggers:

- `recalculate_resource(resource_type)`

It does full recalculation for that resource:

1. Locks stocks by resource (`select_for_update`).
2. Resets all reservations for resource to `0`.
3. Resets allocation/status for active requests of resource.
4. Clears previous transactions for this resource.
5. Re-processes requests in order:
   - urgent first (`is_urgent=True`)
   - then by priority (`CRITICAL > HIGH > NORMAL`)
   - then by creation time

### 2) Allocation from nearest warehouse

For each request, service:

- Finds candidate stocks with matching resource.
- Sorts by geo distance to delivery point.
- Reserves available quantities from nearest warehouses first.
- Writes `ALLOCATION` transactions.

### 3) Critical preemption

If request is `CRITICAL` and still underfilled:

- Reclaims allocations from lower-priority requests.
- Writes `PREEMPT_OUT` and `PREEMPT_IN` transactions.
- Writes allocation history entries.

### 4) Shortage handling

If request is still not fully covered:

- Marks status (`PARTIAL`/`PENDING`)
- Writes `SHORTAGE` transaction.

## API Endpoints

Base prefix: `/api/`

### Warehouses

- `GET /api/warehouses/` - list warehouses with stocks and supplier
- `GET /api/warehouses/{id}/` - warehouse details
- `GET /api/warehouses/nearest/?resource_type=FUEL&latitude=50.45&longitude=30.52&limit=10`
  - Returns nearest warehouses with positive available stock for resource

### Suppliers

- `GET /api/suppliers/` - list suppliers
- `GET /api/suppliers/{id}/` - supplier details

### Delivery Points

- `GET /api/points/` - list delivery points
- `GET /api/points/{id}/` - delivery point details

### Requests

- `GET /api/requests/` - list requests
- `POST /api/requests/` - create request and trigger recalculation
- `GET /api/requests/{id}/` - request details
- `PUT/PATCH /api/requests/{id}/` - update request and trigger recalculation
- `DELETE /api/requests/{id}/` - delete request

Example request payload:

```json
{
  "point": 1,
  "resource_type": "FUEL",
  "quantity_requested": 25,
  "priority": 3,
  "is_urgent": true
}
```

## Concurrency and Integrity

- Transaction boundaries with `transaction.atomic()`
- Row-level locking (`select_for_update`) for stock/request operations
- Indexed fields for scale-sensitive filters (`resource_type`, `priority`, `city`)

## Security Notes (dev vs prod)

Current settings are development-oriented (`DEBUG=True`, permissive CORS). For production:

- Use environment variables for secret/config.
- Set `DEBUG=False`.
- Restrict `ALLOWED_HOSTS` and CORS origins.
- Add authentication/authorization policy for write endpoints.
