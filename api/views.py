from django.contrib.auth import authenticate, logout
from rest_framework import permissions, status, viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from .models import DeliveryPoint, EmployeeProfile, Request, RequestStatus, ResourceTransaction, Stock, Supplier, Warehouse
from .permissions import RequestWritePermission
from .query_services import (
    delivery_points_queryset_for_user,
    requests_queryset_for_user,
    suppliers_queryset_for_user,
    transactions_queryset_for_user,
    warehouses_queryset_for_user,
)
from .serializers import (
    DeliveryPointSerializer,
    LoginRequestSerializer,
    LoginResponseSerializer,
    ApiRootResponseSerializer,
    LogoutResponseSerializer,
    MeResponseSerializer,
    RequestSerializer,
    ResourceTransactionSerializer,
    SupplierSerializer,
    WarehouseSerializer,
)
from .services import LogisticsService
from .utils import calculate_distance


def _command(label, method, path, description, auth_required=True):
    return {
        'label': label,
        'method': method,
        'path': path,
        'description': description,
        'auth_required': auth_required,
    }


class ApiRootView(APIView):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [AllowAny]
    serializer_class = ApiRootResponseSerializer

    @extend_schema(responses={200: ApiRootResponseSerializer})
    def get(self, request):
        profile = getattr(request.user, 'employee_profile', None) if request.user.is_authenticated else None

        commands = [
            _command('login', 'POST', '/api/auth/login/', 'Отримати token для API', False),
            _command('logout', 'POST', '/api/auth/logout/', 'Вийти з сесії або видалити token', False),
            _command('me', 'GET', '/api/auth/me/', 'Поточний користувач', True),
            _command('docs', 'GET', '/api/docs/', 'Swagger UI', True),
            _command('schema', 'GET', '/api/schema/', 'OpenAPI schema', True),
        ]

        if profile is None:
            commands.extend([
                _command('warehouses', 'GET', '/api/warehouses/', 'Склади', True),
                _command('suppliers', 'GET', '/api/suppliers/', 'Постачальники', True),
                _command('points', 'GET', '/api/points/', 'Точки доставки', True),
                _command('transactions', 'GET', '/api/transactions/', 'Транзакції', True),
                _command('requests', 'GET', '/api/requests/', 'Заявки', True),
            ])
        elif profile.role == EmployeeProfile.Role.DELIVERY_POINT_MANAGER:
            commands.extend([
                _command('points', 'GET', '/api/points/', 'Ваша точка доставки', True),
                _command('requests', 'GET/POST', '/api/requests/', 'Ваші заявки', True),
            ])
        elif profile.role == EmployeeProfile.Role.WAREHOUSE_MANAGER:
            commands.extend([
                _command('warehouses', 'GET', '/api/warehouses/', 'Ваш склад', True),
                _command('suppliers', 'GET', '/api/suppliers/', 'Пов’язані постачальники', True),
                _command('requests', 'GET', '/api/requests/', 'Заявки', True),
            ])
        else:
            commands.extend([
                _command('warehouses', 'GET', '/api/warehouses/', 'Склади', True),
                _command('suppliers', 'GET', '/api/suppliers/', 'Постачальники', True),
                _command('points', 'GET', '/api/points/', 'Точки доставки', True),
                _command('transactions', 'GET', '/api/transactions/', 'Транзакції', True),
                _command('requests', 'GET', '/api/requests/', 'Заявки', True),
            ])

        return Response(
            {
                'message': 'API root for development',
                'authenticated': request.user.is_authenticated,
                'user': None if profile is None else {
                    'username': request.user.username,
                    'role': profile.role,
                    'delivery_point_id': profile.delivery_point_id,
                    'warehouse_id': profile.warehouse_id,
                },
                'commands': commands,
            }
        )


class LogoutView(APIView):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [AllowAny]
    serializer_class = LogoutResponseSerializer

    @extend_schema(responses={200: LogoutResponseSerializer})
    def post(self, request):
        if request.user.is_authenticated:
            if request.auth is not None and hasattr(request.auth, 'delete'):
                request.auth.delete()
            logout(request)
        return Response({'detail': 'Вихід виконано'})


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
        return warehouses_queryset_for_user(self.request.user, Warehouse.objects.all())

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

    def get_queryset(self):
        return suppliers_queryset_for_user(self.request.user, Supplier.objects.all())


class ResourceTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ResourceTransaction.objects.select_related('request', 'request__point').all()
    serializer_class = ResourceTransactionSerializer

    def get_queryset(self):
        queryset = transactions_queryset_for_user(self.request.user, super().get_queryset())
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
        return delivery_points_queryset_for_user(self.request.user, DeliveryPoint.objects.all())

# БЛОК ОПЕРАЦІЙ (Створення та перегляд заявок)
class RequestViewSet(viewsets.ModelViewSet):
    """
    Endpoint: /api/requests/
    GET: побачити статус усіх заявок (хто що просив і чи отримав).
    POST: надіслати нову заявку на паливо/товари.
    """
    queryset = Request.objects.select_related('point').all()
    serializer_class = RequestSerializer
    permission_classes = [permissions.IsAuthenticated, RequestWritePermission]

    def get_queryset(self):
        return requests_queryset_for_user(self.request.user)

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
        if serializer.instance.status not in {RequestStatus.PENDING, RequestStatus.PARTIAL}:
            raise ValidationError({'detail': 'Не можна змінювати заявку, яка вже обробляється або виконана.'})

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
        if instance.status not in {RequestStatus.PENDING, RequestStatus.PARTIAL}:
            raise ValidationError({'detail': 'Не можна видаляти заявку, яка вже обробляється або виконана.'})

        resource_type = instance.resource_type
        instance.delete()
        LogisticsService.recalculate_resource(resource_type)