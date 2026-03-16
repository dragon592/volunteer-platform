from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_POST
from django.shortcuts import redirect, render

from .forms import UserRegisterForm
from .services import safe_redirect_target
from .controllers.auth_controller import AuthController


def register_view(request):
    """Регистрация пользователя"""
    return AuthController.register(request)


def login_view(request):
    """Вход пользователя"""
    return AuthController.login(request)


@require_POST
def logout_view(request):
    """Выход пользователя"""
    return AuthController.logout(request)
