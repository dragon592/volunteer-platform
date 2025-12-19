from django.contrib import admin
from .models import Skill, UserProfile, Event, EventRegistration


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']
    search_fields = ['name']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'city', 'phone']
    list_filter = ['role', 'city']
    search_fields = ['user__username', 'user__email', 'city']
    filter_horizontal = ['skills']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'location', 'organizer', 'max_volunteers', 'is_active']
    list_filter = ['is_active', 'date', 'city']
    search_fields = ['title', 'description', 'location']
    filter_horizontal = ['required_skills']
    date_hierarchy = 'date'


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ['volunteer', 'event', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['volunteer__username', 'event__title']
    list_editable = ['status']
