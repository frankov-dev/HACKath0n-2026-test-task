from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render
from .models import DeliveryPoint, Request, ResourceTransaction, Stock, Supplier, Warehouse
from .serializers import DeliveryPointSerializer, RequestSerializer, SupplierSerializer, WarehouseSerializer
from .services import LogisticsService
from .utils import calculate_distance


def dashboard_view(request):
    warehouses = Warehouse.objects.prefetch_related('stocks').order_by('name')
    warehouse_rows = []
    for warehouse in warehouses:
        for stock in warehouse.stocks.all():
            warehouse_rows.append({
                'warehouse_name': warehouse.name,
                'supplier_name': warehouse.supplier.name if warehouse.supplier else '-',
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

    @action(detail=False, methods=['get'], url_path='nearest')
    def nearest(self, request):
        resource_type = request.query_params.get('resource_type')
        latitude = request.query_params.get('latitude')
        longitude = request.query_params.get('longitude')
        limit = int(request.query_params.get('limit', 10))

        if not resource_type or latitude is None or longitude is None:
            return Response(
                {'detail': 'Потрібні параметри: resource_type, latitude, longitude'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            return Response({'detail': 'latitude/longitude мають бути числами'}, status=status.HTTP_400_BAD_REQUEST)

        stocks = (
            Stock.objects.select_related('warehouse')
            .filter(resource_type=resource_type, actual_quantity__gt=0)
        )

        items = []
        for stock in stocks:
            available = stock.available_quantity
            if available <= 0:
                continue
            distance_km = calculate_distance(
                latitude,
                longitude,
                stock.warehouse.latitude,
                stock.warehouse.longitude,
            )
            items.append({
                'warehouse_id': stock.warehouse.id,
                'warehouse_name': stock.warehouse.name,
                'city': stock.warehouse.city,
                'resource_type': resource_type,
                'available_quantity': available,
                'distance_km': round(distance_km, 2),
                'latitude': stock.warehouse.latitude,
                'longitude': stock.warehouse.longitude,
            })

        items.sort(key=lambda x: x['distance_km'])
        return Response(items[:max(limit, 1)])


class SupplierViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

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
        new_request = serializer.save()
        LogisticsService.recalculate_resource(new_request.resource_type)

    def perform_update(self, serializer):
        old_resource_type = serializer.instance.resource_type
        updated_request = serializer.save()

        LogisticsService.recalculate_resource(updated_request.resource_type)
        if old_resource_type != updated_request.resource_type:
            LogisticsService.recalculate_resource(old_resource_type)