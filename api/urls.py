from django.urls import path, include
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.routers import DefaultRouter
from .views import ApiRootView, DeliveryPointViewSet, LoginView, LogoutView, MeView, RequestViewSet, ResourceTransactionViewSet, SupplierViewSet, WarehouseViewSet
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


# Створюємо роутер, який сам збудує правильні шляхи
router = DefaultRouter()

# Реєструємо наші "блоки"
router.register(r'warehouses', WarehouseViewSet, basename='warehouse')
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'transactions', ResourceTransactionViewSet, basename='transaction')
router.register(r'points', DeliveryPointViewSet, basename='point')
router.register(r'requests', RequestViewSet, basename='request')

urlpatterns = [
    path('', ApiRootView.as_view(), name='api-home'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/me/', MeView.as_view(), name='auth-me'),

    # Всі маршрути будуть доступні за префіксом, який ми вкажемо в головному urls.py
    path('', include(router.urls)),

    # Документація
    path(
        'schema/',
        SpectacularAPIView.as_view(
            permission_classes=[IsAuthenticated],
            authentication_classes=[SessionAuthentication, TokenAuthentication],
        ),
        name='schema',
    ),
    path(
        'docs/',
        SpectacularSwaggerView.as_view(
            url_name='schema',
            permission_classes=[IsAuthenticated],
            authentication_classes=[SessionAuthentication, TokenAuthentication],
        ),
        name='swagger-ui',
    ),
]