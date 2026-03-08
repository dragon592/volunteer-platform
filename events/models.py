from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')
    icon = models.CharField(max_length=50, blank=True, verbose_name='Иконка')

    class Meta:
        verbose_name = 'Навык'
        verbose_name_plural = 'Навыки'
        ordering = ['name']

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('volunteer', 'Волонтер'),
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
    xp = models.PositiveIntegerField(default=0, verbose_name='Опыт (XP)')
    level = models.PositiveIntegerField(default=1, verbose_name='Уровень')
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

    @property
    def xp_to_next_level(self):
        next_level_xp = self.level * 100
        return max(next_level_xp - self.xp, 0)

    def recalculate_level(self):
        self.level = max(1, self.xp // 100 + 1)


class Event(models.Model):
    TYPE_CHOICES = [
        ('community', 'Сообщество'),
        ('education', 'Образование'),
        ('ecology', 'Экология'),
        ('health', 'Здоровье'),
        ('charity', 'Благотворительность'),
        ('other', 'Другое'),
    ]

    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    event_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        default='community',
        db_index=True,
        verbose_name='Тип события',
    )
    date = models.DateField(verbose_name='Дата')
    time = models.TimeField(null=True, blank=True, verbose_name='Время')
    location = models.CharField(max_length=200, verbose_name='Место')
    city = models.CharField(max_length=100, blank=True, verbose_name='Город')

    organizer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='organized_events',
        verbose_name='Организатор',
    )
    required_skills = models.ManyToManyField(
        Skill,
        blank=True,
        related_name='events',
        verbose_name='Требуемые навыки',
    )
    max_volunteers = models.PositiveIntegerField(default=10, verbose_name='Макс. волонтеров')
    xp_reward = models.PositiveIntegerField(default=50, verbose_name='XP за участие')

    image_url = models.URLField(blank=True, verbose_name='URL изображения')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'
        ordering = ['date', 'time']
        indexes = [
            models.Index(fields=['is_active', 'date']),
            models.Index(fields=['city']),
        ]

    def __str__(self):
        return self.title

    @property
    def registered_count(self):
        # Reuse annotated value from list views to avoid N+1 counts.
        annotated_count = getattr(self, 'approved_participants', None)
        if annotated_count is not None:
            return annotated_count
        return self.registrations.filter(status__in=['approved', 'completed']).count()

    @property
    def spots_left(self):
        return self.max_volunteers - self.registered_count

    @property
    def is_full(self):
        return self.spots_left <= 0


class EventRegistration(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрено'),
        ('completed', 'Завершено'),
        ('rejected', 'Отклонено'),
        ('cancelled', 'Отменено'),
    ]

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='registrations',
        verbose_name='Событие',
    )
    volunteer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='event_registrations',
        verbose_name='Волонтер',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус',
    )
    message = models.TextField(blank=True, verbose_name='Сообщение')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Завершено в')
    xp_awarded = models.BooleanField(default=False, verbose_name='XP начислен')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Заявка на событие'
        verbose_name_plural = 'Заявки на события'
        unique_together = ['event', 'volunteer']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['volunteer', 'status']),
        ]

    def __str__(self):
        return f'{self.volunteer.username} -> {self.event.title}'


class Achievement(models.Model):
    CATEGORY_CHOICES = [
        ('events_completed', 'Завершенные события'),
        ('xp_total', 'Суммарный XP'),
    ]

    slug = models.SlugField(unique=True, verbose_name='Код')
    title = models.CharField(max_length=120, verbose_name='Название')
    description = models.CharField(max_length=255, verbose_name='Описание')
    icon = models.CharField(max_length=10, default='🏅', verbose_name='Бейдж')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, verbose_name='Категория')
    threshold = models.PositiveIntegerField(default=1, verbose_name='Порог')
    is_active = models.BooleanField(default=True, verbose_name='Активно')

    class Meta:
        verbose_name = 'Достижение'
        verbose_name_plural = 'Достижения'
        ordering = ['category', 'threshold']

    def __str__(self):
        return self.title


class VolunteerAchievement(models.Model):
    volunteer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='volunteer_achievements',
        verbose_name='Волонтер',
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='awards',
        verbose_name='Достижение',
    )
    awarded_at = models.DateTimeField(auto_now_add=True, verbose_name='Выдано')

    class Meta:
        verbose_name = 'Полученное достижение'
        verbose_name_plural = 'Полученные достижения'
        unique_together = ['volunteer', 'achievement']
        ordering = ['-awarded_at']

    def __str__(self):
        return f'{self.volunteer.username} - {self.achievement.title}'


class ChatChannel(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='chat_channels',
        null=True,
        blank=True,
        verbose_name='Событие',
    )
    name = models.CharField(max_length=120, verbose_name='Название канала')
    topic = models.CharField(max_length=255, blank=True, verbose_name='Тема')
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_chat_channels',
        verbose_name='Создан пользователем',
    )
    is_archived = models.BooleanField(default=False, verbose_name='Архивный')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлен')
    participants = models.ManyToManyField(
        User,
        through='ChatChannelMembership',
        related_name='chat_channels',
        verbose_name='Участники',
    )

    class Meta:
        verbose_name = 'Канал чата'
        verbose_name_plural = 'Каналы чата'
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(fields=['event', 'name'], name='unique_channel_name_per_event'),
        ]

    def __str__(self):
        if self.event_id:
            return f'{self.event.title}: {self.name}'
        return self.name


class ChatChannelMembership(models.Model):
    channel = models.ForeignKey(
        ChatChannel,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name='Канал',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_memberships',
        verbose_name='Пользователь',
    )
    notifications_enabled = models.BooleanField(default=True, verbose_name='Уведомления включены')
    last_read_at = models.DateTimeField(default=timezone.now, verbose_name='Последнее чтение')
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name='Вступил')

    class Meta:
        verbose_name = 'Участник канала'
        verbose_name_plural = 'Участники каналов'
        unique_together = ['channel', 'user']
        ordering = ['-joined_at']

    def __str__(self):
        return f'{self.user.username} in {self.channel.name}'


class ChatMessage(models.Model):
    channel = models.ForeignKey(
        ChatChannel,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Канал',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_messages',
        verbose_name='Автор',
    )
    content = models.TextField(verbose_name='Сообщение')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    edited_at = models.DateTimeField(null=True, blank=True, verbose_name='Изменено')

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['channel', 'created_at']),
        ]

    def __str__(self):
        return f'{self.author.username}: {self.content[:40]}'


class Notification(models.Model):
    TYPE_CHOICES = [
        ('application_approved', 'Заявка одобрена'),
        ('application_rejected', 'Заявка отклонена'),
        ('new_application', 'Новая заявка'),
        ('new_event', 'Новое событие'),
        ('event_reminder', 'Напоминание о событии'),
        ('new_message', 'Новое сообщение в чате'),
        ('achievement_unlocked', 'Новое достижение'),
        ('level_up', 'Новый уровень'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Пользователь',
    )
    type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        verbose_name='Тип уведомления',
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
        verbose_name='Связанное событие',
    )
    related_registration = models.ForeignKey(
        EventRegistration,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='Связанная заявка',
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
        icons = {
            'application_approved': '✅',
            'application_rejected': '❌',
            'new_application': '📬',
            'new_event': '🎉',
            'event_reminder': '⏰',
            'new_message': '💬',
            'achievement_unlocked': '🏅',
            'level_up': '⭐',
        }
        return icons.get(self.type, '🔔')


DEFAULT_ACHIEVEMENTS = [
    {
        'slug': 'first_event',
        'title': 'Первый шаг',
        'description': 'Завершено первое событие',
        'icon': '🌱',
        'category': 'events_completed',
        'threshold': 1,
    },
    {
        'slug': 'five_events',
        'title': 'Активный участник',
        'description': 'Завершено 5 событий',
        'icon': '🔥',
        'category': 'events_completed',
        'threshold': 5,
    },
    {
        'slug': 'ten_events',
        'title': 'Опора команды',
        'description': 'Завершено 10 событий',
        'icon': '🏆',
        'category': 'events_completed',
        'threshold': 10,
    },
    {
        'slug': 'xp_250',
        'title': 'Набираю темп',
        'description': 'Получено 250 XP',
        'icon': '⚡',
        'category': 'xp_total',
        'threshold': 250,
    },
    {
        'slug': 'xp_1000',
        'title': 'Мастер волонтерства',
        'description': 'Получено 1000 XP',
        'icon': '👑',
        'category': 'xp_total',
        'threshold': 1000,
    },
]


def ensure_default_achievements():
    for item in DEFAULT_ACHIEVEMENTS:
        Achievement.objects.get_or_create(
            slug=item['slug'],
            defaults={
                'title': item['title'],
                'description': item['description'],
                'icon': item['icon'],
                'category': item['category'],
                'threshold': item['threshold'],
                'is_active': True,
            },
        )


def apply_event_completion_rewards(registration):
    if registration.status != 'completed' or registration.xp_awarded:
        return

    with transaction.atomic():
        profile = registration.volunteer.profile
        previous_level = profile.level
        profile.xp += registration.event.xp_reward
        profile.recalculate_level()
        profile.save(update_fields=['xp', 'level'])

        registration.xp_awarded = True
        if registration.completed_at is None:
            registration.completed_at = timezone.now()
        registration.save(update_fields=['xp_awarded', 'completed_at', 'updated_at'])

        if profile.level > previous_level:
            Notification.objects.create(
                user=registration.volunteer,
                type='level_up',
                title='Новый уровень!',
                message=f'Ваш уровень повышен до {profile.level}.',
                related_event=registration.event,
                related_registration=registration,
            )

        ensure_default_achievements()
        completed_events = EventRegistration.objects.filter(
            volunteer=registration.volunteer,
            status='completed',
        ).count()

        achievements = Achievement.objects.filter(is_active=True)
        for achievement in achievements:
            if achievement.category == 'events_completed' and completed_events < achievement.threshold:
                continue
            if achievement.category == 'xp_total' and profile.xp < achievement.threshold:
                continue

            _, created = VolunteerAchievement.objects.get_or_create(
                volunteer=registration.volunteer,
                achievement=achievement,
            )
            if created:
                Notification.objects.create(
                    user=registration.volunteer,
                    type='achievement_unlocked',
                    title=f'Достижение: {achievement.title}',
                    message=achievement.description,
                    related_event=registration.event,
                    related_registration=registration,
                )


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(post_save, sender=Event)
def create_default_event_channel(sender, instance, created, **kwargs):
    if not created:
        return
    channel = ChatChannel.objects.create(
        event=instance,
        name='Общий',
        topic='Основной канал события',
        created_by=instance.organizer,
    )
    ChatChannelMembership.objects.get_or_create(channel=channel, user=instance.organizer)
