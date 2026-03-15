from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from django.contrib import messages
from django.contrib.auth.models import User

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Кастомный адаптер для социальной аутентификации.
    - Автоматически связывает Google аккаунт с существующим пользователем по email
    - Заполняет имя и фамилию из данных Google
    - Генерирует username если отсутствует
    """

    def pre_social_login(self, request, sociallogin):
        """
        Вызывается перед входом через социальную сеть.
        Если пользователь уже аутентифицирован - ничего не делаем.
        Если аккаунт уже существует - ничего не делаем.
        Если email уже есть в базе - связываем с существующим пользователем.
        """
        if request.user.is_authenticated:
            return

        if sociallogin.is_existing:
            return

        # Получаем email из данных Google
        email = sociallogin.account.extra_data.get('email', '')

        if email:
            try:
                # Проверяем, есть ли пользователь с таким email
                existing_user = User.objects.get(email=email)
                # Проверяем, не привязан ли уже этот социальный аккаунт к другому пользователю
                if SocialAccount.objects.filter(provider=sociallogin.account.provider, uid=sociallogin.account.uid).exists():
                    # Социальный аккаунт уже привязан - показываем ошибку
                    messages.error(request, 'Этот Google аккаунт уже привязан к другому профилю.')
                    return
                # Связываем социальный аккаунт с существующим пользователем
                sociallogin.connect(request, existing_user)
                messages.success(
                    request,
                    f'Добро пожаловать обратно, {existing_user.username}!'
                )
            except User.DoesNotExist:
                # Пользователя с таким email нет - создадим нового
                pass

    def populate_user(self, request, sociallogin, data):
        """
        Заполняем данные пользователя из социального аккаунта.
        """
        user = super().populate_user(request, sociallogin, data)

        # Генерируем username если его нет
        if not user.username:
            email = data.get('email', '')
            if email:
                # Берем часть до @, добавляем случайные цифры если нужно
                base_username = email.split('@')[0]
                username = base_username
                counter = 1
                # Проверяем уникальность
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                user.username = username

        # Заполняем имя и фамилию из данных Google
        user.first_name = data.get('first_name', data.get('given_name', ''))
        user.last_name = data.get('last_name', data.get('family_name', ''))

        return user
