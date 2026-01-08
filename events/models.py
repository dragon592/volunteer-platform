from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Skill(models.Model):
    """Навыки волонтёров (экология, медицина, образование и т.д.)"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')
    icon = models.CharField(max_length=50, blank=True, verbose_name='Иконка')
    
    class Meta:
        verbose_name = 'Навык'
        verbose_name_plural = 'Навыки'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """Профиль пользователя с ролью и навыками"""
    ROLE_CHOICES = [
        ('volunteer', 'Волонтёр'),
        ('organizer', 'Организатор'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='volunteer', verbose_name='Роль')
    bio = models.TextField(blank=True, verbose_name='О себе')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    city = models.CharField(max_length=100, blank=True, verbose_name='Город')
    skills = models.ManyToManyField(Skill, blank=True, related_name='users', verbose_name='Навыки')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Аватар')
    avatar_url = models.URLField(blank=True, verbose_name='Аватар URL (опционально)')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'
    
    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'
    
    @property
    def is_volunteer(self):
        return self.role == 'volunteer'
    
    @property
    def is_organizer(self):
        return self.role == 'organizer'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Автоматическое создание профиля при создании пользователя"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Сохранение профиля при сохранении пользователя"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


class Event(models.Model):
    """Волонтёрское событие"""
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    date = models.DateField(verbose_name='Дата')
    time = models.TimeField(null=True, blank=True, verbose_name='Время')
    location = models.CharField(max_length=200, verbose_name='Место')
    city = models.CharField(max_length=100, blank=True, verbose_name='Город')
    
    organizer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='organized_events',
        verbose_name='Организатор'
    )
    required_skills = models.ManyToManyField(
        Skill, 
        blank=True, 
        related_name='events',
        verbose_name='Требуемые навыки'
    )
    max_volunteers = models.PositiveIntegerField(default=10, verbose_name='Макс. волонтёров')
    
    image_url = models.URLField(blank=True, verbose_name='URL изображения')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'
        ordering = ['date', 'time']
    
    def __str__(self):
        return self.title
    
    @property
    def registered_count(self):
        return self.registrations.filter(status='approved').count()
    
    @property
    def spots_left(self):
        return self.max_volunteers - self.registered_count
    
    @property
    def is_full(self):
        return self.spots_left <= 0


class EventRegistration(models.Model):
    """Заявка волонтёра на событие"""
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
        ('cancelled', 'Отменено'),
    ]
    
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE, 
        related_name='registrations',
        verbose_name='Событие'
    )
    volunteer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='event_registrations',
        verbose_name='Волонтёр'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name='Статус'
    )
    message = models.TextField(blank=True, verbose_name='Сообщение')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Заявка на событие'
        verbose_name_plural = 'Заявки на события'
        unique_together = ['event', 'volunteer']
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.volunteer.username} → {self.event.title}'


class Notification(models.Model):
    """Уведомления для пользователей"""
    TYPE_CHOICES = [
        ('application_approved', 'Заявка одобрена'),
        ('application_rejected', 'Заявка отклонена'),
        ('new_application', 'Новая заявка'),
        ('new_event', 'Новое событие'),
        ('event_reminder', 'Напоминание о событии'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Пользователь'
    )
    type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        verbose_name='Тип уведомления'
    )
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    message = models.TextField(verbose_name='Сообщение')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    related_event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='Связанное событие'
    )
    related_registration = models.ForeignKey(
        EventRegistration,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='Связанная заявка'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    
    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        return f'{self.user.username} - {self.title}'
    
    @property
    def icon(self):
        """Иконка в зависимости от типа"""
        icons = {
            'application_approved': '✅',
            'application_rejected': '❌',
            'new_application': '📬',
            'new_event': '🎉',
            'event_reminder': '⏰',
        }
        return icons.get(self.type, '🔔')
