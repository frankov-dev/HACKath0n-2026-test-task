from rest_framework import serializers
from .models import AllocationHistory, DeliveryPoint, Request, ResourceTransaction, Shipment, Stock, Supplier, Warehouse

# Цей файл необхідний для визначення серіалізаторів, 
# які перетворюють наші моделі в JSON та навпаки. 
# Це дозволяє нам легко обмінюватися даними між фронтендом та бекендом через API.

class StockSerializer(serializers.ModelSerializer):
    """Відображення залишків на складі."""
    resource_type_display = serializers.CharField(source='get_resource_type_display', read_only=True)

    class Meta:
        model = Stock
        fields = ['id', 'resource_type', 'resource_type_display', 'actual_quantity', 'reserved_quantity', 'available_quantity']


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'city', 'latitude', 'longitude']

class WarehouseSerializer(serializers.ModelSerializer):
    """Відображення складу разом із його запасами (вкладені дані)."""
    stocks = StockSerializer(many=True, read_only=True)
    supplier = SupplierSerializer(read_only=True)

    class Meta:
        model = Warehouse
        fields = ['id', 'name', 'city', 'latitude', 'longitude', 'supplier', 'stocks']

class RequestSerializer(serializers.ModelSerializer):
    """Серіалізатор для запитів на ресурси."""
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Request
        fields = [
            'id', 'point', 'resource_type', 'quantity_requested', 
            'quantity_allocated', 'priority', 'priority_display', 
            'is_urgent', 'status', 'status_display', 'created_at'
        ]

        read_only_fields = ['quantity_allocated', 'status', 'created_at']


class ResourceTransactionSerializer(serializers.ModelSerializer):
    resource_type_display = serializers.CharField(source='get_resource_type_display', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    request_point = serializers.CharField(source='request.point.name', read_only=True)
    request_city = serializers.CharField(source='request.point.city', read_only=True)
    request_priority = serializers.CharField(source='request.get_priority_display', read_only=True)
    request_status = serializers.CharField(source='request.get_status_display', read_only=True)

    class Meta:
        model = ResourceTransaction
        fields = [
            'id',
            'request',
            'request_point',
            'request_city',
            'request_priority',
            'request_status',
            'resource_type',
            'resource_type_display',
            'transaction_type',
            'transaction_type_display',
            'quantity',
            'from_location',
            'to_location',
            'note',
            'created_at',
        ]

class DeliveryPointSerializer(serializers.ModelSerializer):
    """Відображення точки доставки (магазину) та її запитів."""
    requests = RequestSerializer(many=True, read_only=True)

    class Meta:
        model = DeliveryPoint
        fields = ['id', 'name', 'city', 'latitude', 'longitude', 'requests']