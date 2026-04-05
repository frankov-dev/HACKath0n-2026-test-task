from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WarehouseViewSet, DeliveryPointViewSet, RequestViewSet

router = DefaultRouter()

router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'points', DeliveryPointViewSet, basename='point')
router.register(r'requests', RequestViewSet, basename='request')

urlpatterns = [
    path('', include(router.urls)),
]