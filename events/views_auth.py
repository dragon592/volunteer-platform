from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_POST
from django.shortcuts import redirect, render

from .forms import UserRegisterForm
from .services import safe_redirect_target


def register_view(request):
    if request.user.is_authenticated:
        return redirect('event_list')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Добро пожаловать! Ваш аккаунт создан.')
            return redirect('profile')
    else:
        form = UserRegisterForm()

    return render(request, 'events/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('event_list')

    next_url = request.POST.get('next') or request.GET.get('next', '')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.get_full_name() or user.username}!')
            return redirect(safe_redirect_target(request))
    else:
        form = AuthenticationForm()

    return render(request, 'events/login.html', {'form': form, 'next_url': next_url})


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, 'Вы вышли из системы.')
    return redirect('event_list')
