from django.test import TestCase

from .models import (
	AllocationHistory,
	DeliveryPoint,
	PriorityLevel,
	Request,
	RequestStatus,
	ResourceType,
	Stock,
	Warehouse,
)
from .services import LogisticsService


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
