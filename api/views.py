from django.shortcuts import render

from rest_framework import viewsets
from .models import Warehouse, DeliveryPoint, Request
from .serializers import WarehouseSerializer, DeliveryPointSerializer, RequestSerializer

class WarehouseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Показує список складів. 
    """
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer

class DeliveryPointViewSet(viewsets.ReadOnlyModelViewSet):
    """Показує список магазинів/АЗС."""
    queryset = DeliveryPoint.objects.all()
    serializer_class = DeliveryPointSerializer

class RequestViewSet(viewsets.ModelViewSet):
    """
    Створення та перегляд запитів на ресурси.
    """
    queryset = Request.objects.all()
    serializer_class = RequestSerializer

    def perform_create(self, serializer):
        # Поки що просто зберігаємо запит.
        # Коли напишемо services.py, додамо сюди авто-перерахунок.
        serializer.save()