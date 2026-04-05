from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
	AllocationHistory,
	DeliveryPoint,
	EmployeeProfile,
	PriorityLevel,
	Request,
	RequestStatus,
	ResourceType,
	TransactionType,
	ResourceTransaction,
	Stock,
	Supplier,
	Warehouse,
)
from .services import LogisticsService
from .test_factories import ApiFactory


class LogisticsServiceTests(TestCase):
	def setUp(self):
		self.point = DeliveryPoint.objects.create(
			name='Точка доставки',
			city='Київ',
			latitude=50.4501,
			longitude=30.5234,
		)

		self.near_warehouse = Warehouse.objects.create(
			name='Ближній склад',
			city='Київ',
			latitude=50.4510,
			longitude=30.5200,
		)
		self.far_warehouse = Warehouse.objects.create(
			name='Далекий склад',
			city='Львів',
			latitude=49.8397,
			longitude=24.0297,
		)

	def test_process_request_uses_nearest_warehouse_first(self):
		near_stock = Stock.objects.create(
			warehouse=self.near_warehouse,
			resource_type=ResourceType.FUEL,
			actual_quantity=5,
			reserved_quantity=0,
		)
		far_stock = Stock.objects.create(
			warehouse=self.far_warehouse,
			resource_type=ResourceType.FUEL,
			actual_quantity=5,
			reserved_quantity=0,
		)
		request = Request.objects.create(
			point=self.point,
			resource_type=ResourceType.FUEL,
			quantity_requested=7,
			priority=PriorityLevel.NORMAL,
		)

		LogisticsService.process_request(request)

		request.refresh_from_db()
		near_stock.refresh_from_db()
		far_stock.refresh_from_db()

		self.assertEqual(request.quantity_allocated, 7)
		self.assertEqual(request.status, RequestStatus.ALLOCATED)
		self.assertEqual(near_stock.reserved_quantity, 5)
		self.assertEqual(far_stock.reserved_quantity, 2)

	def test_process_request_marks_request_partial_when_stock_is_insufficient(self):
		Stock.objects.create(
			warehouse=self.near_warehouse,
			resource_type=ResourceType.GOODS,
			actual_quantity=4,
			reserved_quantity=0,
		)
		request = Request.objects.create(
			point=self.point,
			resource_type=ResourceType.GOODS,
			quantity_requested=7,
			priority=PriorityLevel.HIGH,
		)

		LogisticsService.process_request(request)

		request.refresh_from_db()

		self.assertEqual(request.quantity_allocated, 4)
		self.assertEqual(request.status, RequestStatus.PARTIAL)

	def test_critical_request_takes_quantity_from_lower_priority_requests(self):
		Stock.objects.create(
			warehouse=self.near_warehouse,
			resource_type=ResourceType.SUPPLIES,
			actual_quantity=9,
			reserved_quantity=0,
		)

		normal_request_1 = Request.objects.create(
			point=self.point,
			resource_type=ResourceType.SUPPLIES,
			quantity_requested=3,
			priority=PriorityLevel.NORMAL,
		)
		LogisticsService.process_request(normal_request_1)

		normal_request_2 = Request.objects.create(
			point=self.point,
			resource_type=ResourceType.SUPPLIES,
			quantity_requested=3,
			priority=PriorityLevel.NORMAL,
		)
		LogisticsService.process_request(normal_request_2)

		normal_request_3 = Request.objects.create(
			point=self.point,
			resource_type=ResourceType.SUPPLIES,
			quantity_requested=3,
			priority=PriorityLevel.NORMAL,
		)
		LogisticsService.process_request(normal_request_3)

		critical_request = Request.objects.create(
			point=self.point,
			resource_type=ResourceType.SUPPLIES,
			quantity_requested=7,
			priority=PriorityLevel.CRITICAL,
		)

		LogisticsService.process_request(critical_request)

		normal_request_1.refresh_from_db()
		normal_request_2.refresh_from_db()
		normal_request_3.refresh_from_db()
		critical_request.refresh_from_db()

		self.assertEqual(critical_request.quantity_allocated, 7)
		self.assertEqual(critical_request.status, RequestStatus.ALLOCATED)
		self.assertEqual(normal_request_1.quantity_allocated, 0)
		self.assertEqual(normal_request_1.status, RequestStatus.PENDING)
		self.assertEqual(normal_request_2.quantity_allocated, 0)
		self.assertEqual(normal_request_2.status, RequestStatus.PENDING)
		self.assertEqual(normal_request_3.quantity_allocated, 2)
		self.assertEqual(normal_request_3.status, RequestStatus.PARTIAL)

		critical_history = AllocationHistory.objects.filter(request=critical_request)
		donor_history = AllocationHistory.objects.filter(request__in=[normal_request_1, normal_request_2, normal_request_3])

		self.assertEqual(critical_history.count(), 3)
		self.assertEqual(donor_history.count(), 3)

	def test_recalculate_resource_prioritizes_urgent_requests(self):
		Stock.objects.create(
			warehouse=self.near_warehouse,
			resource_type=ResourceType.GOODS,
			actual_quantity=6,
			reserved_quantity=0,
		)

		normal_request = Request.objects.create(
			point=self.point,
			resource_type=ResourceType.GOODS,
			quantity_requested=6,
			priority=PriorityLevel.HIGH,
			is_urgent=False,
		)
		urgent_request = Request.objects.create(
			point=self.point,
			resource_type=ResourceType.GOODS,
			quantity_requested=6,
			priority=PriorityLevel.HIGH,
			is_urgent=True,
		)

		LogisticsService.recalculate_resource(ResourceType.GOODS)

		normal_request.refresh_from_db()
		urgent_request.refresh_from_db()

		self.assertEqual(urgent_request.quantity_allocated, 6)
		self.assertEqual(urgent_request.status, RequestStatus.ALLOCATED)
		self.assertEqual(normal_request.quantity_allocated, 0)
		self.assertEqual(normal_request.status, RequestStatus.PENDING)

	def test_recalculate_resource_updates_allocation_when_demand_changes(self):
		Stock.objects.create(
			warehouse=self.near_warehouse,
			resource_type=ResourceType.FUEL,
			actual_quantity=10,
			reserved_quantity=0,
		)

		request_a = Request.objects.create(
			point=self.point,
			resource_type=ResourceType.FUEL,
			quantity_requested=5,
			priority=PriorityLevel.HIGH,
		)
		request_b = Request.objects.create(
			point=self.point,
			resource_type=ResourceType.FUEL,
			quantity_requested=5,
			priority=PriorityLevel.NORMAL,
		)

		LogisticsService.recalculate_resource(ResourceType.FUEL)

		request_a.quantity_requested = 8
		request_a.save(update_fields=['quantity_requested'])

		LogisticsService.recalculate_resource(ResourceType.FUEL)

		request_a.refresh_from_db()
		request_b.refresh_from_db()

		self.assertEqual(request_a.quantity_allocated, 8)
		self.assertEqual(request_b.quantity_allocated, 2)
		self.assertEqual(request_a.status, RequestStatus.ALLOCATED)
		self.assertEqual(request_b.status, RequestStatus.PARTIAL)

		self.assertTrue(
			ResourceTransaction.objects.filter(
				request=request_b,
				transaction_type=TransactionType.SHORTAGE,
			).exists()
		)


class AuthAndRBACApiTests(APITestCase):
	def setUp(self):
		self.point_kyiv = ApiFactory.create_point(name='АЗС Київ')
		self.point_lviv = ApiFactory.create_point(
			name='АЗС Львів',
			city='Львів',
			latitude=49.84,
			longitude=24.03,
		)

		warehouse = ApiFactory.create_warehouse(name='Київський хаб')
		Stock.objects.create(
			warehouse=warehouse,
			resource_type=ResourceType.FUEL,
			actual_quantity=100,
			reserved_quantity=0,
		)

		self.dispatcher = ApiFactory.create_user_with_role(
			username='dispatcher_test',
			password='Dispatcher123!',
			role=EmployeeProfile.Role.DISPATCHER,
		)

		self.point_manager = ApiFactory.create_user_with_role(
			username='point_manager_test',
			password='PointManager123!',
			role=EmployeeProfile.Role.DELIVERY_POINT_MANAGER,
			delivery_point=self.point_kyiv,
		)

		self.warehouse_manager = ApiFactory.create_user_with_role(
			username='warehouse_manager_test',
			password='WarehouseManager123!',
			role=EmployeeProfile.Role.WAREHOUSE_MANAGER,
			warehouse=warehouse,
		)

		self.req_kyiv = ApiFactory.create_request(
			point=self.point_kyiv,
			resource_type=ResourceType.FUEL,
			quantity_requested=10,
			priority=PriorityLevel.NORMAL,
		)
		self.req_lviv = ApiFactory.create_request(
			point=self.point_lviv,
			resource_type=ResourceType.FUEL,
			quantity_requested=10,
			priority=PriorityLevel.NORMAL,
		)

	def test_login_returns_token(self):
		response = self.client.post(
			reverse('auth-login'),
			{'username': 'dispatcher_test', 'password': 'Dispatcher123!'},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('token', response.data)

	def test_api_root_is_public_and_lists_commands(self):
		response = self.client.get(reverse('api-home'))
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('commands', response.data)
		self.assertTrue(any(command['label'] == 'login' for command in response.data['commands']))

	def test_logout_clears_session(self):
		self.assertTrue(self.client.login(username='dispatcher_test', password='Dispatcher123!'))
		response = self.client.post(reverse('auth-logout'))
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertFalse('_auth_user_id' in self.client.session)

	def test_requests_endpoint_requires_token(self):
		response = self.client.get(reverse('request-list'))
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_point_manager_sees_only_own_point_requests(self):
		self.client.force_authenticate(user=self.point_manager)
		response = self.client.get(reverse('request-list'))
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]['point'], self.point_kyiv.id)

	def test_point_manager_create_request_auto_binds_own_point(self):
		self.client.force_authenticate(user=self.point_manager)
		response = self.client.post(
			reverse('request-list'),
			{
				'point': self.point_lviv.id,
				'resource_type': ResourceType.FUEL,
				'quantity_requested': 5,
				'priority': PriorityLevel.HIGH,
				'is_urgent': False,
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		created = Request.objects.get(id=response.data['id'])
		self.assertEqual(created.point_id, self.point_kyiv.id)

	def test_warehouse_manager_cannot_create_request(self):
		self.client.force_authenticate(user=self.warehouse_manager)
		response = self.client.post(
			reverse('request-list'),
			{
				'point': self.point_kyiv.id,
				'resource_type': ResourceType.FUEL,
				'quantity_requested': 5,
				'priority': PriorityLevel.NORMAL,
				'is_urgent': False,
			},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ApiCoverageAndRedistributionTests(APITestCase):
	def setUp(self):
		self.supplier = Supplier.objects.create(
			name='Постачальник Київ',
			city='Київ',
			latitude=50.45,
			longitude=30.52,
		)
		self.warehouse_kyiv = Warehouse.objects.create(
			name='Склад Київ',
			city='Київ',
			latitude=50.45,
			longitude=30.52,
			supplier=self.supplier,
		)
		self.warehouse_lviv = Warehouse.objects.create(
			name='Склад Львів',
			city='Львів',
			latitude=49.84,
			longitude=24.03,
			supplier=self.supplier,
		)

		Stock.objects.create(
			warehouse=self.warehouse_kyiv,
			resource_type=ResourceType.FUEL,
			actual_quantity=100,
			reserved_quantity=0,
		)
		Stock.objects.create(
			warehouse=self.warehouse_kyiv,
			resource_type=ResourceType.SUPPLIES,
			actual_quantity=9,
			reserved_quantity=0,
		)

		self.point_kyiv = ApiFactory.create_point(
			name='Точка Київ',
			latitude=50.40,
			longitude=30.60,
		)
		self.point_lviv = ApiFactory.create_point(
			name='Точка Львів',
			city='Львів',
			latitude=49.83,
			longitude=24.01,
		)

		self.dispatcher = ApiFactory.create_user_with_role(
			username='dispatcher_cov',
			password='Dispatcher123!',
			role=EmployeeProfile.Role.DISPATCHER,
		)

		self.point_manager = ApiFactory.create_user_with_role(
			username='point_cov',
			password='PointManager123!',
			role=EmployeeProfile.Role.DELIVERY_POINT_MANAGER,
			delivery_point=self.point_kyiv,
		)

		self.warehouse_manager = ApiFactory.create_user_with_role(
			username='warehouse_cov',
			password='WarehouseManager123!',
			role=EmployeeProfile.Role.WAREHOUSE_MANAGER,
			warehouse=self.warehouse_kyiv,
		)

		self.req_kyiv = ApiFactory.create_request(
			point=self.point_kyiv,
			resource_type=ResourceType.FUEL,
			quantity_requested=10,
			priority=PriorityLevel.NORMAL,
		)
		self.req_lviv = ApiFactory.create_request(
			point=self.point_lviv,
			resource_type=ResourceType.FUEL,
			quantity_requested=10,
			priority=PriorityLevel.NORMAL,
		)
		LogisticsService.recalculate_resource(ResourceType.FUEL)

	def _login_and_set_token(self, username, password):
		response = self.client.post(
			reverse('auth-login'),
			{'username': username, 'password': password},
			format='json',
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		token = response.data['token']
		self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
		return token

	def test_all_roles_can_login_and_access_all_main_api_endpoints(self):
		roles = [
			('dispatcher_cov', 'Dispatcher123!', 2, 200, 200, 200, 200),
			('point_cov', 'PointManager123!', 1, 200, 404, 200, 200),
			('warehouse_cov', 'WarehouseManager123!', 2, 200, 200, 200, 200),
		]

		for username, password, expected_requests_count, expected_warehouse_list, expected_warehouse_detail, expected_supplier_list, expected_point_list in roles:
			with self.subTest(username=username):
				self._login_and_set_token(username, password)

				me_response = self.client.get(reverse('auth-me'))
				self.assertEqual(me_response.status_code, status.HTTP_200_OK)

				self.assertEqual(self.client.get(reverse('warehouse-list')).status_code, expected_warehouse_list)
				self.assertEqual(self.client.get(reverse('warehouse-detail', args=[self.warehouse_kyiv.id])).status_code, expected_warehouse_detail)
				self.assertEqual(self.client.get(reverse('supplier-list')).status_code, expected_supplier_list)
				self.assertEqual(self.client.get(reverse('point-list')).status_code, expected_point_list)

				nearest_response = self.client.get(
					reverse('warehouse-nearest'),
					{
						'resource_type': ResourceType.FUEL,
						'latitude': 50.40,
						'longitude': 30.60,
						'limit': 5,
					},
				)
				self.assertEqual(nearest_response.status_code, status.HTTP_200_OK)

				requests_response = self.client.get(reverse('request-list'))
				self.assertEqual(requests_response.status_code, status.HTTP_200_OK)
				self.assertEqual(len(requests_response.data), expected_requests_count)

				transactions_response = self.client.get(reverse('transaction-list'))
				self.assertEqual(transactions_response.status_code, status.HTTP_200_OK)

				schema_response = self.client.get(reverse('schema'))
				self.assertEqual(schema_response.status_code, status.HTTP_200_OK)

				docs_response = self.client.get(reverse('swagger-ui'))
				self.assertEqual(docs_response.status_code, status.HTTP_200_OK)

				self.client.credentials()

	def test_critical_request_redistribution_logic(self):
		normal_request_1 = Request.objects.create(
			point=self.point_kyiv,
			resource_type=ResourceType.SUPPLIES,
			quantity_requested=3,
			priority=PriorityLevel.NORMAL,
		)
		LogisticsService.process_request(normal_request_1)

		normal_request_2 = Request.objects.create(
			point=self.point_kyiv,
			resource_type=ResourceType.SUPPLIES,
			quantity_requested=3,
			priority=PriorityLevel.NORMAL,
		)
		LogisticsService.process_request(normal_request_2)

		normal_request_3 = Request.objects.create(
			point=self.point_kyiv,
			resource_type=ResourceType.SUPPLIES,
			quantity_requested=3,
			priority=PriorityLevel.NORMAL,
		)
		LogisticsService.process_request(normal_request_3)

		critical_request = Request.objects.create(
			point=self.point_lviv,
			resource_type=ResourceType.SUPPLIES,
			quantity_requested=7,
			priority=PriorityLevel.CRITICAL,
		)
		LogisticsService.process_request(critical_request)

		critical_request.refresh_from_db()
		normal_request_1.refresh_from_db()
		normal_request_2.refresh_from_db()
		normal_request_3.refresh_from_db()

		self.assertEqual(critical_request.quantity_allocated, 7)
		self.assertEqual(critical_request.status, RequestStatus.ALLOCATED)
		self.assertEqual(normal_request_1.quantity_allocated, 0)
		self.assertEqual(normal_request_2.quantity_allocated, 0)
		self.assertEqual(normal_request_3.quantity_allocated, 2)

		self.assertTrue(
			ResourceTransaction.objects.filter(
				request=critical_request,
				transaction_type=TransactionType.PREEMPT_IN,
			).exists()
		)
		self.assertTrue(
			ResourceTransaction.objects.filter(
				request__in=[normal_request_1, normal_request_2, normal_request_3],
				transaction_type=TransactionType.PREEMPT_OUT,
			).exists()
		)
