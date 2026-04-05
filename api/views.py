from django.contrib.auth import authenticate
from rest_framework import permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from .models import DeliveryPoint, EmployeeProfile, Request, ResourceTransaction, Stock, Supplier, Warehouse
from .serializers import (
    DeliveryPointSerializer,
    LoginRequestSerializer,
    LoginResponseSerializer,
    MeResponseSerializer,
    RequestSerializer,
    ResourceTransactionSerializer,
    SupplierSerializer,
    WarehouseSerializer,
)
from .services import LogisticsService
from .utils import calculate_distance


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(request=LoginRequestSerializer, responses={200: LoginResponseSerializer})
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            raise ValidationError({'detail': 'Потрібні username і password'})

        user = authenticate(request, username=username, password=password)
        if user is None:
            raise ValidationError({'detail': 'Невірний логін або пароль'})

        token, _ = Token.objects.get_or_create(user=user)
        profile = getattr(user, 'employee_profile', None)

        return Response(
            {
                'token': token.key,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': profile.role if profile else None,
                    'delivery_point_id': profile.delivery_point_id if profile else None,
                    'warehouse_id': profile.warehouse_id if profile else None,
                },
            }
        )


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: MeResponseSerializer})
    def get(self, request):
        profile = getattr(request.user, 'employee_profile', None)
        return Response(
            {
                'id': request.user.id,
                'username': request.user.username,
                'role': profile.role if profile else None,
                'delivery_point_id': profile.delivery_point_id if profile else None,
                'warehouse_id': profile.warehouse_id if profile else None,
            }
        )


def get_user_profile_or_none(user):
    return getattr(user, 'employee_profile', None)

# БЛОК КАТАЛОГУ (Тільки перегляд)
class WarehouseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint: /api/warehouses/
    Для фронтенду: вивести список складів та залишки на них.
    """
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer

    def get_queryset(self):
        user = self.request.user
        profile = get_user_profile_or_none(user)

        if user.is_superuser:
            return Warehouse.objects.all()
        if profile is None:
            return Warehouse.objects.none()
        if profile.role == EmployeeProfile.Role.DISPATCHER:
            return Warehouse.objects.all()
        if profile.role == EmployeeProfile.Role.WAREHOUSE_MANAGER:
            if profile.warehouse_id is None:
                return Warehouse.objects.none()
            return Warehouse.objects.filter(id=profile.warehouse_id)
        return Warehouse.objects.none()

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
            .filter(resource_type=resource_type, actual_quantity__gt=0, warehouse__in=self.get_queryset())
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

    def get_queryset(self):
        user = self.request.user
        profile = get_user_profile_or_none(user)

        if user.is_superuser:
            return Supplier.objects.all()
        if profile is None:
            return Supplier.objects.none()
        if profile.role == EmployeeProfile.Role.DISPATCHER:
            return Supplier.objects.all()
        if profile.role == EmployeeProfile.Role.WAREHOUSE_MANAGER and profile.warehouse_id is not None:
            return Supplier.objects.filter(warehouses__id=profile.warehouse_id).distinct()
        return Supplier.objects.none()


class ResourceTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ResourceTransaction.objects.select_related('request', 'request__point').all()
    serializer_class = ResourceTransactionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        resource_type = self.request.query_params.get('resource_type')
        request_id = self.request.query_params.get('request')
        transaction_type = self.request.query_params.get('transaction_type')

        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        if request_id:
            queryset = queryset.filter(request_id=request_id)
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)

        return queryset.order_by('-created_at')

class DeliveryPointViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint: /api/points/
    Для фронтенду: вивести список магазинів/АЗС, щоб вибрати 'себе'.
    """
    queryset = DeliveryPoint.objects.all()
    serializer_class = DeliveryPointSerializer

    def get_queryset(self):
        user = self.request.user
        profile = get_user_profile_or_none(user)

        if user.is_superuser:
            return DeliveryPoint.objects.all()
        if profile is None:
            return DeliveryPoint.objects.none()
        if profile.role == EmployeeProfile.Role.DISPATCHER:
            return DeliveryPoint.objects.all()
        if profile.role == EmployeeProfile.Role.DELIVERY_POINT_MANAGER:
            if profile.delivery_point_id is None:
                return DeliveryPoint.objects.none()
            return DeliveryPoint.objects.filter(id=profile.delivery_point_id)
        return DeliveryPoint.objects.none()

# БЛОК ОПЕРАЦІЙ (Створення та перегляд заявок)
class RequestViewSet(viewsets.ModelViewSet):
    """
    Endpoint: /api/requests/
    GET: побачити статус усіх заявок (хто що просив і чи отримав).
    POST: надіслати нову заявку на паливо/товари.
    """
    queryset = Request.objects.select_related('point').all()
    serializer_class = RequestSerializer

    def get_queryset(self):
        base_queryset = Request.objects.select_related('point').all()
        user = self.request.user
        profile = get_user_profile_or_none(user)

        if user.is_superuser:
            return base_queryset

        if profile is None:
            return Request.objects.none()

        if profile.role == EmployeeProfile.Role.DISPATCHER:
            return base_queryset

        if profile.role == EmployeeProfile.Role.DELIVERY_POINT_MANAGER:
            if profile.delivery_point_id is None:
                return Request.objects.none()
            return base_queryset.filter(point_id=profile.delivery_point_id)

        if profile.role == EmployeeProfile.Role.WAREHOUSE_MANAGER:
            return base_queryset

        return Request.objects.none()

    def perform_create(self, serializer):
        profile = get_user_profile_or_none(self.request.user)

        if profile and profile.role == EmployeeProfile.Role.DELIVERY_POINT_MANAGER:
            if profile.delivery_point_id is None:
                raise PermissionDenied('Менеджер точки не прив’язаний до жодної точки доставки')
            new_request = serializer.save(point_id=profile.delivery_point_id)
        else:
            new_request = serializer.save()

        LogisticsService.recalculate_resource(new_request.resource_type)

    def perform_update(self, serializer):
        profile = get_user_profile_or_none(self.request.user)
        old_resource_type = serializer.instance.resource_type

        if profile and profile.role == EmployeeProfile.Role.DELIVERY_POINT_MANAGER:
            if profile.delivery_point_id is None:
                raise PermissionDenied('Менеджер точки не прив’язаний до жодної точки доставки')
            updated_request = serializer.save(point_id=profile.delivery_point_id)
        else:
            updated_request = serializer.save()

        LogisticsService.recalculate_resource(updated_request.resource_type)
        if old_resource_type != updated_request.resource_type:
            LogisticsService.recalculate_resource(old_resource_type)

    def perform_destroy(self, instance):
        resource_type = instance.resource_type
        instance.delete()
        LogisticsService.recalculate_resource(resource_type)