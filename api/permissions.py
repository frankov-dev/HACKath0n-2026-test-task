from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import EmployeeProfile


def get_user_profile(user):
    return getattr(user, 'employee_profile', None)


class RequestWritePermission(BasePermission):
    """Allow request mutations only for dispatcher and delivery point manager."""

    message = 'Недостатньо прав для зміни заявок'

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        profile = get_user_profile(user)
        if profile is None:
            return False

        return profile.role in {
            EmployeeProfile.Role.DISPATCHER,
            EmployeeProfile.Role.DELIVERY_POINT_MANAGER,
        }
