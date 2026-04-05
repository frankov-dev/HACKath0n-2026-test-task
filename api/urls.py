from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DeliveryPointViewSet, RequestViewSet, SupplierViewSet, WarehouseViewSet
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


# Створюємо роутер, який сам збудує правильні шляхи
router = DefaultRouter()

# Реєструємо наші "блоки"
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'points', DeliveryPointViewSet, basename='point')
router.register(r'requests', RequestViewSet, basename='request')

urlpatterns = [
    # Всі маршрути будуть доступні за префіксом, який ми вкажемо в головному urls.py
    path('', include(router.urls)),

    # Документація
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]