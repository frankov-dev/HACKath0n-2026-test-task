from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import OperationalError
from django.urls import reverse
from rest_framework.test import APIClient

from api.models import DeliveryPoint, EmployeeProfile, Request, ResourceType, Stock, Supplier, Warehouse


class Command(BaseCommand):
    help = "Runs smoke checks for API auth, role access, and key endpoints"

    def handle(self, *args, **options):
        # Ensure DB schema exists before smoke checks.
        call_command("migrate", interactive=False, verbosity=0)

        # APIClient sends requests with host=testserver by default.
        if "testserver" not in settings.ALLOWED_HOSTS:
            settings.ALLOWED_HOSTS.append("testserver")

        self._ensure_demo_data()

        client = APIClient()
        results = []

        users = [
            {
                "username": "dispatcher_admin",
                "password": "Dispatcher123!",
                "role": EmployeeProfile.Role.DISPATCHER,
            },
            {
                "username": "manager_kyiv_point",
                "password": "PointManager123!",
                "role": EmployeeProfile.Role.DELIVERY_POINT_MANAGER,
            },
            {
                "username": "manager_lviv_warehouse",
                "password": "WarehouseManager123!",
                "role": EmployeeProfile.Role.WAREHOUSE_MANAGER,
            },
        ]

        # Unauthenticated check (all API except login must be protected)
        unauth_resp = client.get(reverse("request-list"))
        results.append(("unauthenticated request-list returns 401", unauth_resp.status_code == 401, f"status={unauth_resp.status_code}"))

        try:
            first_warehouse = Warehouse.objects.first()
            first_point = DeliveryPoint.objects.first()
            first_request = Request.objects.first()
        except OperationalError as exc:
            self.stderr.write(f"Database is not ready: {exc}")
            raise SystemExit(1)

        for user_data in users:
            username = user_data["username"]
            password = user_data["password"]
            expected_role = user_data["role"]

            login_resp = client.post(
                reverse("auth-login"),
                {"username": username, "password": password},
                format="json",
            )

            login_ok = login_resp.status_code == 200 and "token" in login_resp.data
            results.append((f"{username} login", login_ok, f"status={login_resp.status_code}"))
            if not login_ok:
                continue

            token = login_resp.data["token"]
            client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

            me_resp = client.get(reverse("auth-me"))
            me_ok = (
                me_resp.status_code == 200
                and me_resp.data.get("username") == username
                and me_resp.data.get("role") == expected_role
            )
            results.append((f"{username} auth-me", me_ok, f"status={me_resp.status_code}"))

            checks = [
                ("warehouse-list", reverse("warehouse-list"), {}),
                ("supplier-list", reverse("supplier-list"), {}),
                ("point-list", reverse("point-list"), {}),
                ("transaction-list", reverse("transaction-list"), {}),
                (
                    "warehouse-nearest",
                    reverse("warehouse-nearest"),
                    {
                        "resource_type": "FUEL",
                        "latitude": 50.45,
                        "longitude": 30.52,
                        "limit": 5,
                    },
                ),
                ("request-list", reverse("request-list"), {}),
                ("schema", reverse("schema"), {}),
                ("swagger-ui", reverse("swagger-ui"), {}),
            ]

            for label, path, params in checks:
                resp = client.get(path, params)
                results.append((f"{username} GET {label}", resp.status_code == 200, f"status={resp.status_code}"))

            if first_warehouse is not None:
                resp = client.get(reverse("warehouse-detail", args=[first_warehouse.id]))
                results.append((f"{username} GET warehouse-detail", resp.status_code == 200, f"status={resp.status_code}"))

            if first_point is not None:
                resp = client.get(reverse("point-detail", args=[first_point.id]))
                results.append((f"{username} GET point-detail", resp.status_code == 200, f"status={resp.status_code}"))

            if first_request is not None:
                resp = client.get(reverse("request-detail", args=[first_request.id]))
                expected_ok = resp.status_code == 200
                profile = EmployeeProfile.objects.filter(user__username=username).select_related("delivery_point").first()
                if profile and profile.role == EmployeeProfile.Role.DELIVERY_POINT_MANAGER:
                    expected_ok = (resp.status_code == 200) == (first_request.point_id == profile.delivery_point_id)
                results.append((f"{username} GET request-detail role-scope", expected_ok, f"status={resp.status_code}"))

            list_resp = client.get(reverse("request-list"))
            expected_count = Request.objects.count()
            profile = EmployeeProfile.objects.filter(user__username=username).select_related("delivery_point").first()
            if profile and profile.role == EmployeeProfile.Role.DELIVERY_POINT_MANAGER:
                expected_count = Request.objects.filter(point_id=profile.delivery_point_id).count()
            count_ok = list_resp.status_code == 200 and len(list_resp.data) == expected_count
            results.append((f"{username} request-list count by role", count_ok, f"got={len(list_resp.data) if list_resp.status_code == 200 else 'n/a'} expected={expected_count}"))

            if profile and profile.role == EmployeeProfile.Role.DELIVERY_POINT_MANAGER:
                other_point = DeliveryPoint.objects.exclude(id=profile.delivery_point_id).first()
                if other_point is not None:
                    create_resp = client.post(
                        reverse("request-list"),
                        {
                            "point": other_point.id,
                            "resource_type": "FUEL",
                            "quantity_requested": 3,
                            "priority": 2,
                            "is_urgent": False,
                        },
                        format="json",
                    )
                    created_ok = create_resp.status_code == 201
                    if created_ok:
                        created_ok = create_resp.data.get("point") == profile.delivery_point_id
                    results.append((f"{username} create request auto-point bind", created_ok, f"status={create_resp.status_code}"))

            client.credentials()

        # Redistribution check
        distribution_ok, details = self._check_critical_redistribution()
        results.append(("critical request redistribution", distribution_ok, details))

        passed = sum(1 for _, ok, _ in results if ok)
        total = len(results)

        self.stdout.write("\nSmoke API results:\n")
        for name, ok, detail in results:
            status_txt = "PASS" if ok else "FAIL"
            self.stdout.write(f"[{status_txt}] {name} ({detail})")

        self.stdout.write(f"\nSummary: {passed}/{total} passed")
        if passed != total:
            raise SystemExit(1)

    def _ensure_demo_data(self):
        supplier, _ = Supplier.objects.get_or_create(
            name="Smoke Supplier Kyiv",
            defaults={"city": "Київ", "latitude": 50.45, "longitude": 30.52},
        )

        warehouse_kyiv, _ = Warehouse.objects.get_or_create(
            name="Smoke Warehouse Kyiv",
            defaults={
                "city": "Київ",
                "latitude": 50.45,
                "longitude": 30.52,
                "supplier": supplier,
            },
        )
        if warehouse_kyiv.supplier_id is None:
            warehouse_kyiv.supplier = supplier
            warehouse_kyiv.save(update_fields=["supplier"])

        warehouse_lviv, _ = Warehouse.objects.get_or_create(
            name="Smoke Warehouse Lviv",
            defaults={
                "city": "Львів",
                "latitude": 49.84,
                "longitude": 24.03,
                "supplier": supplier,
            },
        )

        point_kyiv, _ = DeliveryPoint.objects.get_or_create(
            name="Smoke Point Kyiv",
            defaults={"city": "Київ", "latitude": 50.40, "longitude": 30.60},
        )
        point_lviv, _ = DeliveryPoint.objects.get_or_create(
            name="Smoke Point Lviv",
            defaults={"city": "Львів", "latitude": 49.83, "longitude": 24.01},
        )

        for resource, qty in ((ResourceType.FUEL, 100.0), (ResourceType.SUPPLIES, 9.0)):
            stock, _ = Stock.objects.get_or_create(
                warehouse=warehouse_kyiv,
                resource_type=resource,
                defaults={"actual_quantity": qty, "reserved_quantity": 0.0},
            )
            if stock.actual_quantity < qty:
                stock.actual_quantity = qty
                stock.save(update_fields=["actual_quantity"])

        if not Request.objects.exists():
            Request.objects.create(
                point=point_kyiv,
                resource_type=ResourceType.FUEL,
                quantity_requested=10,
                priority=1,
            )
            Request.objects.create(
                point=point_lviv,
                resource_type=ResourceType.FUEL,
                quantity_requested=10,
                priority=1,
            )

        self._ensure_user(
            username="dispatcher_admin",
            password="Dispatcher123!",
            role=EmployeeProfile.Role.DISPATCHER,
        )
        self._ensure_user(
            username="manager_kyiv_point",
            password="PointManager123!",
            role=EmployeeProfile.Role.DELIVERY_POINT_MANAGER,
            delivery_point=point_kyiv,
        )
        self._ensure_user(
            username="manager_lviv_warehouse",
            password="WarehouseManager123!",
            role=EmployeeProfile.Role.WAREHOUSE_MANAGER,
            warehouse=warehouse_lviv,
        )

    def _ensure_user(self, username, password, role, delivery_point=None, warehouse=None):
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password(password)
            user.save()
        profile, _ = EmployeeProfile.objects.get_or_create(user=user, defaults={"role": role})

        updated_fields = []
        if profile.role != role:
            profile.role = role
            updated_fields.append("role")
        if profile.delivery_point_id != (delivery_point.id if delivery_point else None):
            profile.delivery_point = delivery_point
            updated_fields.append("delivery_point")
        if profile.warehouse_id != (warehouse.id if warehouse else None):
            profile.warehouse = warehouse
            updated_fields.append("warehouse")
        if updated_fields:
            profile.save(update_fields=updated_fields)

    def _check_critical_redistribution(self):
        # Isolated scenario with unique resource type SUPPLIES to avoid conflicting with existing requests.
        kyiv_point = DeliveryPoint.objects.filter(city="Київ").first() or DeliveryPoint.objects.first()
        lviv_point = DeliveryPoint.objects.filter(city="Львів").first() or DeliveryPoint.objects.last()
        warehouse = Warehouse.objects.first()

        if kyiv_point is None or lviv_point is None or warehouse is None:
            return False, "missing base data for redistribution scenario"

        stock, _ = warehouse.stocks.get_or_create(
            resource_type="SUPPLIES",
            defaults={"actual_quantity": 9.0, "reserved_quantity": 0.0},
        )
        stock.actual_quantity = 9.0
        stock.reserved_quantity = 0.0
        stock.save(update_fields=["actual_quantity", "reserved_quantity"])

        for old in Request.objects.filter(resource_type="SUPPLIES"):
            old.delete()

        normal_1 = Request.objects.create(
            point=kyiv_point,
            resource_type="SUPPLIES",
            quantity_requested=3,
            priority=1,
        )
        normal_2 = Request.objects.create(
            point=kyiv_point,
            resource_type="SUPPLIES",
            quantity_requested=3,
            priority=1,
        )
        normal_3 = Request.objects.create(
            point=kyiv_point,
            resource_type="SUPPLIES",
            quantity_requested=3,
            priority=1,
        )
        critical = Request.objects.create(
            point=lviv_point,
            resource_type="SUPPLIES",
            quantity_requested=7,
            priority=3,
        )

        from api.services import LogisticsService

        LogisticsService.process_request(normal_1)
        LogisticsService.process_request(normal_2)
        LogisticsService.process_request(normal_3)
        LogisticsService.process_request(critical)

        normal_1.refresh_from_db()
        normal_2.refresh_from_db()
        normal_3.refresh_from_db()
        critical.refresh_from_db()

        ok = (
            critical.quantity_allocated == 7
            and critical.status == "ALLOCATED"
            and normal_1.quantity_allocated == 0
            and normal_2.quantity_allocated == 0
            and normal_3.quantity_allocated == 2
        )
        detail = (
            f"critical={critical.quantity_allocated}/{critical.quantity_requested}, "
            f"donors=({normal_1.quantity_allocated}, {normal_2.quantity_allocated}, {normal_3.quantity_allocated})"
        )
        return ok, detail
