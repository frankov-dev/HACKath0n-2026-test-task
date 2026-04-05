from django.shortcuts import render
from rest_framework import viewsets
from .models import DeliveryPoint, Request, ResourceTransaction, Warehouse
from .serializers import WarehouseSerializer, DeliveryPointSerializer, RequestSerializer
from .services import LogisticsService


def dashboard_view(request):
    warehouses = Warehouse.objects.prefetch_related('stocks').order_by('name')
    warehouse_rows = []
    for warehouse in warehouses:
        for stock in warehouse.stocks.all():
            warehouse_rows.append({
                'warehouse_name': warehouse.name,
                'city': warehouse.city,
                'resource_type': stock.get_resource_type_display(),
                'actual': stock.actual_quantity,
                'reserved': stock.reserved_quantity,
                'available': stock.available_quantity,
            })

    transactions_qs = ResourceTransaction.objects.select_related('request').order_by('-created_at')[:200]
    transaction_rows = []
    for tx in transactions_qs:
        transaction_rows.append({
            'id': tx.id,
            'created_at': tx.created_at,
            'resource_type': tx.get_resource_type_display(),
            'transaction_type': tx.get_transaction_type_display(),
            'quantity': tx.quantity,
            'from_location': tx.from_location,
            'to_location': tx.to_location,
            'request_id': tx.request_id,
            'note': tx.note,
        })

    requests_qs = Request.objects.select_related('point').prefetch_related('transactions').order_by('-created_at')[:100]
    request_rows = []
    for req in requests_qs:
        tx_flow = []
        for tx in req.transactions.all().order_by('created_at'):
            tx_flow.append(
                f"{tx.from_location} -> {tx.to_location}: {tx.quantity} ({tx.get_transaction_type_display()})"
            )

        request_rows.append({
            'id': req.id,
            'point_name': req.point.name,
            'city': req.point.city,
            'resource_type': req.get_resource_type_display(),
            'requested': req.quantity_requested,
            'allocated': req.quantity_allocated,
            'priority': req.get_priority_display(),
            'urgent': req.is_urgent,
            'status': req.get_status_display(),
            'flow_lines': tx_flow,
            'created_at': req.created_at,
        })

    return render(
        request,
        'api/dashboard.html',
        {
            'warehouse_rows': warehouse_rows,
            'transaction_rows': transaction_rows,
            'request_rows': request_rows,
        },
    )

# БЛОК КАТАЛОГУ (Тільки перегляд)
class WarehouseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint: /api/warehouses/
    Для фронтенду: вивести список складів та залишки на них.
    """
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer

class DeliveryPointViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint: /api/points/
    Для фронтенду: вивести список магазинів/АЗС, щоб вибрати 'себе'.
    """
    queryset = DeliveryPoint.objects.all()
    serializer_class = DeliveryPointSerializer

# БЛОК ОПЕРАЦІЙ (Створення та перегляд заявок)
class RequestViewSet(viewsets.ModelViewSet):
    """
    Endpoint: /api/requests/
    GET: побачити статус усіх заявок (хто що просив і чи отримав).
    POST: надіслати нову заявку на паливо/товари.
    """
    queryset = Request.objects.all()
    serializer_class = RequestSerializer

    def perform_create(self, serializer):
        # 1. Зберігаємо запит в базу
        new_request = serializer.save()
        
        # 2. Запускаємо наш "розумний" сервіс
        LogisticsService.process_request(new_request)