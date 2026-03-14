class LoginRequiredMiddleware:
    """
    Middleware для принудительной аутентификации.
    Все страницы требуют входа, кроме:
    - Страницы входа/регистрации
    - Страницы allauth (/accounts/)
    - Статические файлы
    - Медиа файлы
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # URL которые не требуют аутентификации (строковые пути)
        self.exempt_urls = [
            '/accounts/',  # allauth URLs (includes Google OAuth callbacks)
            '/login/',     # custom login view
            '/register/',  # custom register view
            '/static/',
            '/media/',
        ]

    def __call__(self, request):
        path = request.path_info

        # Проверяем, является ли текущий URL исключением
        if any(path.startswith(url) for url in self.exempt_urls):
            return self.get_response(request)

        # Проверяем, соответствует ли путь именам login или register (view names)
        # Используем resolver для определения имени URL
        try:
            from django.urls import resolve
            resolver_match = resolve(path)
            if resolver_match.url_name in ['login', 'register']:
                return self.get_response(request)
        except Exception:
            # Если resolve не сработал, продолжаем проверку
            pass

        # Если пользователь не аутентифицирован - перенаправляем на страницу входа
        if not request.user.is_authenticated:
            return redirect(f'/login/?next={request.path}')

        return self.get_response(request)
