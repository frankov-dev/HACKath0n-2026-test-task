from django.contrib.auth.models import User

from .models import DeliveryPoint, EmployeeProfile, Request, Warehouse


class ApiFactory:
    @staticmethod
    def create_point(name='Точка', city='Київ', latitude=50.45, longitude=30.52):
        return DeliveryPoint.objects.create(
            name=name,
            city=city,
            latitude=latitude,
            longitude=longitude,
        )

    @staticmethod
    def create_warehouse(name='Склад', city='Київ', latitude=50.45, longitude=30.52, supplier=None):
        return Warehouse.objects.create(
            name=name,
            city=city,
            latitude=latitude,
            longitude=longitude,
            supplier=supplier,
        )

    @staticmethod
    def create_user_with_role(
        username,
        password,
        role,
        delivery_point=None,
        warehouse=None,
    ):
        user = User.objects.create_user(username=username, password=password)
        EmployeeProfile.objects.create(
            user=user,
            role=role,
            delivery_point=delivery_point,
            warehouse=warehouse,
        )
        return user

    @staticmethod
    def create_request(point, resource_type, quantity_requested, priority, is_urgent=False):
        return Request.objects.create(
            point=point,
            resource_type=resource_type,
            quantity_requested=quantity_requested,
            priority=priority,
            is_urgent=is_urgent,
        )
