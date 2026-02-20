from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='РќР°Р·РІР°РЅРёРµ')
    icon = models.CharField(max_length=50, blank=True, verbose_name='РРєРѕРЅРєР°')

    class Meta:
        verbose_name = 'РќР°РІС‹Рє'
        verbose_name_plural = 'РќР°РІС‹РєРё'
        ordering = ['name']

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('volunteer', 'Р’РѕР»РѕРЅС‚РµСЂ'),
        ('organizer', 'РћСЂРіР°РЅРёР·Р°С‚РѕСЂ'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='volunteer', verbose_name='Р РѕР»СЊ')
    bio = models.TextField(blank=True, verbose_name='Рћ СЃРµР±Рµ')
    phone = models.CharField(max_length=20, blank=True, verbose_name='РўРµР»РµС„РѕРЅ')
    city = models.CharField(max_length=100, blank=True, verbose_name='Р“РѕСЂРѕРґ')
    skills = models.ManyToManyField(Skill, blank=True, related_name='users', verbose_name='РќР°РІС‹РєРё')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='РђРІР°С‚Р°СЂ')
    avatar_url = models.URLField(blank=True, verbose_name='РђРІР°С‚Р°СЂ URL (РѕРїС†РёРѕРЅР°Р»СЊРЅРѕ)')
    xp = models.PositiveIntegerField(default=0, verbose_name='РћРїС‹С‚ (XP)')
    level = models.PositiveIntegerField(default=1, verbose_name='РЈСЂРѕРІРµРЅСЊ')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'РџСЂРѕС„РёР»СЊ'
        verbose_name_plural = 'РџСЂРѕС„РёР»Рё'

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
        ('community', 'РЎРѕРѕР±С‰РµСЃС‚РІРѕ'),
        ('education', 'РћР±СЂР°Р·РѕРІР°РЅРёРµ'),
        ('ecology', 'Р­РєРѕР»РѕРіРёСЏ'),
        ('health', 'Р—РґРѕСЂРѕРІСЊРµ'),
        ('charity', 'Р‘Р»Р°РіРѕС‚РІРѕСЂРёС‚РµР»СЊРЅРѕСЃС‚СЊ'),
        ('other', 'Р”СЂСѓРіРѕРµ'),
    ]

    title = models.CharField(max_length=200, verbose_name='РќР°Р·РІР°РЅРёРµ')
    description = models.TextField(verbose_name='РћРїРёСЃР°РЅРёРµ')
    event_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        default='community',
        db_index=True,
        verbose_name='РўРёРї СЃРѕР±С‹С‚РёСЏ',
    )
    date = models.DateField(verbose_name='Р”Р°С‚Р°')
    time = models.TimeField(null=True, blank=True, verbose_name='Р’СЂРµРјСЏ')
    location = models.CharField(max_length=200, verbose_name='РњРµСЃС‚Рѕ')
    city = models.CharField(max_length=100, blank=True, verbose_name='Р“РѕСЂРѕРґ')

    organizer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='organized_events',
        verbose_name='РћСЂРіР°РЅРёР·Р°С‚РѕСЂ',
    )
    required_skills = models.ManyToManyField(
        Skill,
        blank=True,
        related_name='events',
        verbose_name='РўСЂРµР±СѓРµРјС‹Рµ РЅР°РІС‹РєРё',
    )
    max_volunteers = models.PositiveIntegerField(default=10, verbose_name='РњР°РєСЃ. РІРѕР»РѕРЅС‚РµСЂРѕРІ')
    xp_reward = models.PositiveIntegerField(default=50, verbose_name='XP Р·Р° СѓС‡Р°СЃС‚РёРµ')

    image_url = models.URLField(blank=True, verbose_name='URL РёР·РѕР±СЂР°Р¶РµРЅРёСЏ')
    is_active = models.BooleanField(default=True, verbose_name='РђРєС‚РёРІРЅРѕ')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'РЎРѕР±С‹С‚РёРµ'
        verbose_name_plural = 'РЎРѕР±С‹С‚РёСЏ'
        ordering = ['date', 'time']

    def __str__(self):
        return self.title

    @property
    def registered_count(self):
        return self.registrations.filter(status__in=['approved', 'completed']).count()

    @property
    def spots_left(self):
        return self.max_volunteers - self.registered_count

    @property
    def is_full(self):
        return self.spots_left <= 0


class EventRegistration(models.Model):
    STATUS_CHOICES = [
        ('pending', 'РќР° СЂР°СЃСЃРјРѕС‚СЂРµРЅРёРё'),
        ('approved', 'РћРґРѕР±СЂРµРЅРѕ'),
        ('completed', 'Р—Р°РІРµСЂС€РµРЅРѕ'),
        ('rejected', 'РћС‚РєР»РѕРЅРµРЅРѕ'),
        ('cancelled', 'РћС‚РјРµРЅРµРЅРѕ'),
    ]

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='registrations',
        verbose_name='РЎРѕР±С‹С‚РёРµ',
    )
    volunteer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='event_registrations',
        verbose_name='Р’РѕР»РѕРЅС‚РµСЂ',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='РЎС‚Р°С‚СѓСЃ',
    )
    message = models.TextField(blank=True, verbose_name='РЎРѕРѕР±С‰РµРЅРёРµ')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Р—Р°РІРµСЂС€РµРЅРѕ РІ')
    xp_awarded = models.BooleanField(default=False, verbose_name='XP РЅР°С‡РёСЃР»РµРЅ')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Р—Р°СЏРІРєР° РЅР° СЃРѕР±С‹С‚РёРµ'
        verbose_name_plural = 'Р—Р°СЏРІРєРё РЅР° СЃРѕР±С‹С‚РёСЏ'
        unique_together = ['event', 'volunteer']
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.volunteer.username} -> {self.event.title}'


class Achievement(models.Model):
    CATEGORY_CHOICES = [
        ('events_completed', 'Р—Р°РІРµСЂС€РµРЅРЅС‹Рµ СЃРѕР±С‹С‚РёСЏ'),
        ('xp_total', 'РЎСѓРјРјР°СЂРЅС‹Р№ XP'),
    ]

    slug = models.SlugField(unique=True, verbose_name='РљРѕРґ')
    title = models.CharField(max_length=120, verbose_name='РќР°Р·РІР°РЅРёРµ')
    description = models.CharField(max_length=255, verbose_name='РћРїРёСЃР°РЅРёРµ')
    icon = models.CharField(max_length=10, default='рџЏ…', verbose_name='Р‘РµР№РґР¶')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, verbose_name='РљР°С‚РµРіРѕСЂРёСЏ')
    threshold = models.PositiveIntegerField(default=1, verbose_name='РџРѕСЂРѕРі')
    is_active = models.BooleanField(default=True, verbose_name='РђРєС‚РёРІРЅРѕ')

    class Meta:
        verbose_name = 'Р”РѕСЃС‚РёР¶РµРЅРёРµ'
        verbose_name_plural = 'Р”РѕСЃС‚РёР¶РµРЅРёСЏ'
        ordering = ['category', 'threshold']

    def __str__(self):
        return self.title


class VolunteerAchievement(models.Model):
    volunteer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='volunteer_achievements',
        verbose_name='Р’РѕР»РѕРЅС‚РµСЂ',
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='awards',
        verbose_name='Р”РѕСЃС‚РёР¶РµРЅРёРµ',
    )
    awarded_at = models.DateTimeField(auto_now_add=True, verbose_name='Р’С‹РґР°РЅРѕ')

    class Meta:
        verbose_name = 'РџРѕР»СѓС‡РµРЅРЅРѕРµ РґРѕСЃС‚РёР¶РµРЅРёРµ'
        verbose_name_plural = 'РџРѕР»СѓС‡РµРЅРЅС‹Рµ РґРѕСЃС‚РёР¶РµРЅРёСЏ'
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
        verbose_name='РЎРѕР±С‹С‚РёРµ',
    )
    name = models.CharField(max_length=120, verbose_name='РќР°Р·РІР°РЅРёРµ РєР°РЅР°Р»Р°')
    topic = models.CharField(max_length=255, blank=True, verbose_name='РўРµРјР°')
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_chat_channels',
        verbose_name='РЎРѕР·РґР°РЅ РїРѕР»СЊР·РѕРІР°С‚РµР»РµРј',
    )
    is_archived = models.BooleanField(default=False, verbose_name='РђСЂС…РёРІРЅС‹Р№')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='РЎРѕР·РґР°РЅ')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='РћР±РЅРѕРІР»РµРЅ')
    participants = models.ManyToManyField(
        User,
        through='ChatChannelMembership',
        related_name='chat_channels',
        verbose_name='РЈС‡Р°СЃС‚РЅРёРєРё',
    )

    class Meta:
        verbose_name = 'РљР°РЅР°Р» С‡Р°С‚Р°'
        verbose_name_plural = 'РљР°РЅР°Р»С‹ С‡Р°С‚Р°'
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
        verbose_name='РљР°РЅР°Р»',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_memberships',
        verbose_name='РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ',
    )
    notifications_enabled = models.BooleanField(default=True, verbose_name='РЈРІРµРґРѕРјР»РµРЅРёСЏ РІРєР»СЋС‡РµРЅС‹')
    last_read_at = models.DateTimeField(default=timezone.now, verbose_name='РџРѕСЃР»РµРґРЅРµРµ С‡С‚РµРЅРёРµ')
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name='Р’СЃС‚СѓРїРёР»')

    class Meta:
        verbose_name = 'РЈС‡Р°СЃС‚РЅРёРє РєР°РЅР°Р»Р°'
        verbose_name_plural = 'РЈС‡Р°СЃС‚РЅРёРєРё РєР°РЅР°Р»РѕРІ'
        unique_together = ['channel', 'user']
        ordering = ['-joined_at']

    def __str__(self):
        return f'{self.user.username} in {self.channel.name}'


class ChatMessage(models.Model):
    channel = models.ForeignKey(
        ChatChannel,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='РљР°РЅР°Р»',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_messages',
        verbose_name='РђРІС‚РѕСЂ',
    )
    content = models.TextField(verbose_name='РЎРѕРѕР±С‰РµРЅРёРµ')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='РЎРѕР·РґР°РЅРѕ')
    edited_at = models.DateTimeField(null=True, blank=True, verbose_name='РР·РјРµРЅРµРЅРѕ')

    class Meta:
        verbose_name = 'РЎРѕРѕР±С‰РµРЅРёРµ'
        verbose_name_plural = 'РЎРѕРѕР±С‰РµРЅРёСЏ'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['channel', 'created_at']),
        ]

    def __str__(self):
        return f'{self.author.username}: {self.content[:40]}'


class Notification(models.Model):
    TYPE_CHOICES = [
        ('application_approved', 'Р—Р°СЏРІРєР° РѕРґРѕР±СЂРµРЅР°'),
        ('application_rejected', 'Р—Р°СЏРІРєР° РѕС‚РєР»РѕРЅРµРЅР°'),
        ('new_application', 'РќРѕРІР°СЏ Р·Р°СЏРІРєР°'),
        ('new_event', 'РќРѕРІРѕРµ СЃРѕР±С‹С‚РёРµ'),
        ('event_reminder', 'РќР°РїРѕРјРёРЅР°РЅРёРµ Рѕ СЃРѕР±С‹С‚РёРё'),
        ('new_message', 'РќРѕРІРѕРµ СЃРѕРѕР±С‰РµРЅРёРµ РІ С‡Р°С‚Рµ'),
        ('achievement_unlocked', 'РќРѕРІРѕРµ РґРѕСЃС‚РёР¶РµРЅРёРµ'),
        ('level_up', 'РќРѕРІС‹Р№ СѓСЂРѕРІРµРЅСЊ'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ',
    )
    type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        verbose_name='РўРёРї СѓРІРµРґРѕРјР»РµРЅРёСЏ',
    )
    title = models.CharField(max_length=200, verbose_name='Р—Р°РіРѕР»РѕРІРѕРє')
    message = models.TextField(verbose_name='РЎРѕРѕР±С‰РµРЅРёРµ')
    is_read = models.BooleanField(default=False, verbose_name='РџСЂРѕС‡РёС‚Р°РЅРѕ')
    related_event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='РЎРІСЏР·Р°РЅРЅРѕРµ СЃРѕР±С‹С‚РёРµ',
    )
    related_registration = models.ForeignKey(
        EventRegistration,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='РЎРІСЏР·Р°РЅРЅР°СЏ Р·Р°СЏРІРєР°',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='РЎРѕР·РґР°РЅРѕ')

    class Meta:
        verbose_name = 'РЈРІРµРґРѕРјР»РµРЅРёРµ'
        verbose_name_plural = 'РЈРІРµРґРѕРјР»РµРЅРёСЏ'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.title}'

    @property
    def icon(self):
        icons = {
            'application_approved': 'вњ…',
            'application_rejected': 'вќЊ',
            'new_application': 'рџ“¬',
            'new_event': 'рџЋ‰',
            'event_reminder': 'вЏ°',
            'new_message': 'рџ’¬',
            'achievement_unlocked': 'рџЏ…',
            'level_up': 'в­ђ',
        }
        return icons.get(self.type, 'рџ””')


DEFAULT_ACHIEVEMENTS = [
    {
        'slug': 'first_event',
        'title': 'РџРµСЂРІС‹Р№ С€Р°Рі',
        'description': 'Р—Р°РІРµСЂС€РµРЅРѕ РїРµСЂРІРѕРµ СЃРѕР±С‹С‚РёРµ',
        'icon': 'рџЊ±',
        'category': 'events_completed',
        'threshold': 1,
    },
    {
        'slug': 'five_events',
        'title': 'РђРєС‚РёРІРЅС‹Р№ СѓС‡Р°СЃС‚РЅРёРє',
        'description': 'Р—Р°РІРµСЂС€РµРЅРѕ 5 СЃРѕР±С‹С‚РёР№',
        'icon': 'рџ”Ґ',
        'category': 'events_completed',
        'threshold': 5,
    },
    {
        'slug': 'ten_events',
        'title': 'РћРїРѕСЂР° РєРѕРјР°РЅРґС‹',
        'description': 'Р—Р°РІРµСЂС€РµРЅРѕ 10 СЃРѕР±С‹С‚РёР№',
        'icon': 'рџЏ†',
        'category': 'events_completed',
        'threshold': 10,
    },
    {
        'slug': 'xp_250',
        'title': 'РќР°Р±РёСЂР°СЋ С‚РµРјРї',
        'description': 'РџРѕР»СѓС‡РµРЅРѕ 250 XP',
        'icon': 'вљЎ',
        'category': 'xp_total',
        'threshold': 250,
    },
    {
        'slug': 'xp_1000',
        'title': 'РњР°СЃС‚РµСЂ РІРѕР»РѕРЅС‚РµСЂСЃС‚РІР°',
        'description': 'РџРѕР»СѓС‡РµРЅРѕ 1000 XP',
        'icon': 'рџ‘‘',
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
                title='РќРѕРІС‹Р№ СѓСЂРѕРІРµРЅСЊ!',
                message=f'Р’Р°С€ СѓСЂРѕРІРµРЅСЊ РїРѕРІС‹С€РµРЅ РґРѕ {profile.level}.',
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
                    title=f'Р”РѕСЃС‚РёР¶РµРЅРёРµ: {achievement.title}',
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
        name='РћР±С‰РёР№',
        topic='РћСЃРЅРѕРІРЅРѕР№ РєР°РЅР°Р» СЃРѕР±С‹С‚РёСЏ',
        created_by=instance.organizer,
    )
    ChatChannelMembership.objects.get_or_create(channel=channel, user=instance.organizer)
