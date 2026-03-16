"""
Сериализаторы для событий (API валидация и преобразование).
"""
from rest_framework import serializers
from django.utils import timezone
from events.models import Event, EventRegistration, Skill
from events.validators.event_validators import (
    validate_event_date,
    validate_max_volunteers,
    validate_xp_reward
)


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'icon']


class EventListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка событий"""
    organizer_name = serializers.CharField(source='organizer.get_full_name', read_only=True)
    organizer_username = serializers.CharField(source='organizer.username', read_only=True)
    registered_count = serializers.IntegerField(read_only=True)
    spots_left = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    required_skills_details = SkillSerializer(many=True, source='required_skills', read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'event_type', 'date', 'time',
            'location', 'city', 'organizer_name', 'organizer_username',
            'max_volunteers', 'xp_reward', 'image_url', 'is_active',
            'registered_count', 'spots_left', 'is_full',
            'required_skills_details', 'created_at'
        ]
        read_only_fields = ['created_at']


class EventDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детального просмотра события"""
    organizer = serializers.SerializerMethodField()
    required_skills = SkillSerializer(many=True, read_only=True)
    registered_count = serializers.IntegerField(read_only=True)
    spots_left = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    user_registration = serializers.SerializerMethodField()
    can_register = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'event_type', 'date', 'time',
            'location', 'city', 'organizer', 'required_skills',
            'max_volunteers', 'xp_reward', 'image_url', 'is_active',
            'registered_count', 'spots_left', 'is_full',
            'user_registration', 'can_register', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_organizer(self, obj):
        return {
            'id': obj.organizer.id,
            'username': obj.organizer.username,
            'full_name': obj.organizer.get_full_name() or obj.organizer.username,
            'avatar': obj.organizer.profile.avatar.url if hasattr(obj.organizer, 'profile') and obj.organizer.profile.avatar else None
        }
    
    def get_user_registration(self, obj):
        """Возвращает информацию о регистрации текущего пользователя"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            registration = EventRegistration.objects.get(
                event=obj,
                volunteer=request.user
            )
            return {
                'id': registration.id,
                'status': registration.status,
                'message': registration.message,
                'created_at': registration.created_at.isoformat()
            }
        except EventRegistration.DoesNotExist:
            return None
    
    def get_can_register(self, obj):
        """Проверяет, может ли текущий пользователь зарегистрироваться"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'profile') or not request.user.profile.is_volunteer:
            return False
        if obj.is_full:
            return False
        if obj.date < timezone.localdate():
            return False
        
        # Проверяем существование активной регистрации
        active_registration = EventRegistration.objects.filter(
            event=obj,
            volunteer=request.user,
            status__in=['pending', 'approved', 'completed']
        ).exists()
        
        return not active_registration


class EventCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления события"""
    
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'event_type', 'date', 'time',
            'location', 'city', 'required_skills', 'max_volunteers',
            'xp_reward', 'image_url', 'is_active'
        ]
    
    def validate_date(self, value):
        validate_event_date(value)
        return value
    
    def validate_max_volunteers(self, value):
        validate_max_volunteers(value)
        return value
    
    def validate_xp_reward(self, value):
        validate_xp_reward(value)
        return value
    
    def validate(self, data):
        """Дополнительная валидация"""
        # Если обновляем событие, проверяем что не меняем организатора
        if self.instance and 'organizer' in data:
            if data['organizer'] != self.instance.organizer:
                raise serializers.ValidationError(
                    'Изменение организатора запрещено.'
                )
        return data
    
    def create(self, validated_data):
        """Создание события с обработкой ManyToMany полей"""
        skills = validated_data.pop('required_skills', [])
        event = Event.objects.create(**validated_data)
        event.required_skills.set(skills)
        return event
    
    def update(self, instance, validated_data):
        """Обновление события"""
        skills = validated_data.pop('required_skills', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if skills is not None:
            instance.required_skills.set(skills)
        
        return instance
