from django.contrib import admin
<<<<<<< HEAD

from .models import (
    Achievement,
    ChatChannel,
    ChatChannelMembership,
    ChatMessage,
    Event,
    EventRegistration,
    Notification,
    Skill,
    UserProfile,
    VolunteerAchievement,
)
=======
from .models import Skill, UserProfile, Event, EventRegistration, Notification
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']
    search_fields = ['name']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
<<<<<<< HEAD
    list_display = ['user', 'role', 'city', 'phone', 'level', 'xp']
    list_filter = ['role', 'city', 'level']
=======
    list_display = ['user', 'role', 'city', 'phone']
    list_filter = ['role', 'city']
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    search_fields = ['user__username', 'user__email', 'city']
    filter_horizontal = ['skills']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
<<<<<<< HEAD
    list_display = ['title', 'event_type', 'date', 'location', 'organizer', 'max_volunteers', 'xp_reward', 'is_active']
    list_filter = ['event_type', 'is_active', 'date', 'city']
=======
    list_display = ['title', 'date', 'location', 'organizer', 'max_volunteers', 'is_active']
    list_filter = ['is_active', 'date', 'city']
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    search_fields = ['title', 'description', 'location']
    filter_horizontal = ['required_skills']
    date_hierarchy = 'date'


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
<<<<<<< HEAD
    list_display = ['volunteer', 'event', 'status', 'xp_awarded', 'created_at']
    list_filter = ['status', 'xp_awarded', 'created_at']
    search_fields = ['volunteer__username', 'event__title']
    list_editable = ['status', 'xp_awarded']
=======
    list_display = ['volunteer', 'event', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['volunteer__username', 'event__title']
    list_editable = ['status']
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'title', 'is_read', 'created_at']
    list_filter = ['type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    list_editable = ['is_read']
    readonly_fields = ['created_at']
<<<<<<< HEAD


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'threshold', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['title', 'description', 'slug']
    prepopulated_fields = {'slug': ['title']}


@admin.register(VolunteerAchievement)
class VolunteerAchievementAdmin(admin.ModelAdmin):
    list_display = ['volunteer', 'achievement', 'awarded_at']
    list_filter = ['achievement__category', 'awarded_at']
    search_fields = ['volunteer__username', 'achievement__title']


@admin.register(ChatChannel)
class ChatChannelAdmin(admin.ModelAdmin):
    list_display = ['name', 'event', 'created_by', 'is_archived', 'updated_at']
    list_filter = ['is_archived', 'created_at']
    search_fields = ['name', 'topic', 'event__title']


@admin.register(ChatChannelMembership)
class ChatChannelMembershipAdmin(admin.ModelAdmin):
    list_display = ['channel', 'user', 'notifications_enabled', 'last_read_at', 'joined_at']
    list_filter = ['notifications_enabled', 'joined_at']
    search_fields = ['channel__name', 'user__username']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['channel', 'author', 'created_at']
    list_filter = ['created_at']
    search_fields = ['channel__name', 'author__username', 'content']
=======
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
