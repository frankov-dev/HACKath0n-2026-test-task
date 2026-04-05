from .models import EmployeeProfile, Request


def _profile(user):
    return getattr(user, 'employee_profile', None)


def requests_queryset_for_user(user):
    qs = Request.objects.select_related('point').all()

    if user.is_superuser:
        return qs

    profile = _profile(user)
    if profile is None:
        return qs.none()

    if profile.role in {
        EmployeeProfile.Role.DISPATCHER,
        EmployeeProfile.Role.WAREHOUSE_MANAGER,
    }:
        return qs

    if profile.role == EmployeeProfile.Role.DELIVERY_POINT_MANAGER:
        if profile.delivery_point_id:
            return qs.filter(point_id=profile.delivery_point_id)
        return qs.none()

    return qs.none()


def warehouses_queryset_for_user(user, base_queryset):
    if user.is_superuser:
        return base_queryset

    profile = _profile(user)
    if profile is None:
        return base_queryset.none()

    if profile.role == EmployeeProfile.Role.DISPATCHER:
        return base_queryset

    if profile.role == EmployeeProfile.Role.WAREHOUSE_MANAGER:
        if profile.warehouse_id:
            return base_queryset.filter(id=profile.warehouse_id)
        return base_queryset.none()

    return base_queryset.none()


def suppliers_queryset_for_user(user, base_queryset):
    if user.is_superuser:
        return base_queryset

    profile = _profile(user)
    if profile is None:
        return base_queryset.none()

    if profile.role == EmployeeProfile.Role.DISPATCHER:
        return base_queryset

    if profile.role == EmployeeProfile.Role.WAREHOUSE_MANAGER and profile.warehouse_id:
        return base_queryset.filter(warehouses__id=profile.warehouse_id).distinct()

    return base_queryset.none()


def delivery_points_queryset_for_user(user, base_queryset):
    if user.is_superuser:
        return base_queryset

    profile = _profile(user)
    if profile is None:
        return base_queryset.none()

    if profile.role == EmployeeProfile.Role.DISPATCHER:
        return base_queryset

    if profile.role == EmployeeProfile.Role.DELIVERY_POINT_MANAGER:
        if profile.delivery_point_id:
            return base_queryset.filter(id=profile.delivery_point_id)
        return base_queryset.none()

    return base_queryset.none()


def transactions_queryset_for_user(user, base_queryset):
    if user.is_superuser:
        return base_queryset

    profile = _profile(user)
    if profile is None:
        return base_queryset.none()

    if profile.role in {
        EmployeeProfile.Role.DISPATCHER,
        EmployeeProfile.Role.WAREHOUSE_MANAGER,
    }:
        return base_queryset

    if profile.role == EmployeeProfile.Role.DELIVERY_POINT_MANAGER:
        if profile.delivery_point_id:
            return base_queryset.filter(request__point_id=profile.delivery_point_id)
        return base_queryset.none()

    return base_queryset.none()
