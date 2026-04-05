from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import redirect, render
from rest_framework.authtoken.models import Token

from .models import EmployeeProfile

# Known credentials from seed_db.py. They are shown only in DEBUG mode.
DEMO_CREDENTIALS = {
    'dispatcher_admin': 'Dispatcher123!',
    'manager_kyiv_point': 'PointManager123!',
    'manager_lviv_warehouse': 'WarehouseManager123!',
}


def _role_for_user(user):
    profile = getattr(user, 'employee_profile', None)
    if profile is None:
        return '-'
    return profile.role


def dev_portal(request):
    if not settings.DEBUG:
        raise Http404()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'login':
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '').strip()
            user = authenticate(request, username=username, password=password)

            if user is None:
                messages.error(request, 'Невірний логін або пароль')
            else:
                login(request, user)
                messages.success(request, f'Увійшли як {user.username}')
                return redirect('dev-portal')

        if action == 'logout':
            logout(request)
            messages.success(request, 'Вихід виконано')
            return redirect('dev-portal')

    users_for_view = []
    for user in User.objects.all().order_by('username'):
        users_for_view.append(
            {
                'username': user.username,
                'role': _role_for_user(user),
                'known_password': DEMO_CREDENTIALS.get(user.username, '(невідомо)'),
            }
        )

    current_token = None
    if request.user.is_authenticated:
        token, _ = Token.objects.get_or_create(user=request.user)
        current_token = token.key

    context = {
        'is_debug': settings.DEBUG,
        'users_for_view': users_for_view,
        'current_token': current_token,
    }
    return render(request, 'api/dev_portal.html', context)
