from rest_framework import viewsets
from .models import Warehouse, DeliveryPoint, Request
from .serializers import WarehouseSerializer, DeliveryPointSerializer, RequestSerializer
from .services import LogisticsService

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