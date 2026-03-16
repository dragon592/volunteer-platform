"""
Сериализаторы для регистраций на события.
"""
from rest_framework import serializers
from events.models import EventRegistration
from events.validators.event_validators import validate_date_range


class EventRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для заявки на участие"""
    volunteer_name = serializers.CharField(source='volunteer.get_full_name', read_only=True)
    volunteer_username = serializers.CharField(source='volunteer.username', read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    
    class Meta:
        model = EventRegistration
        fields = [
            'id', 'event', 'volunteer', 'status', 'message',
            'volunteer_name', 'volunteer_username', 'event_title',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['volunteer', 'status', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Создание заявки - volunteer берется из текущего пользователя"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError('Требуется аутентификация.')
        
        validated_data['volunteer'] = request.user
        return super().create(validated_data)


class EventRegistrationUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления статуса заявки (только для организаторов)"""
    
    class Meta:
        model = EventRegistration
        fields = ['status']
    
    def validate_status(self, value):
        """Валидация статуса"""
        allowed_statuses = ['approved', 'rejected', 'completed']
        if value not in allowed_statuses:
            raise serializers.ValidationError(
                f'Недопустимый статус. Разрешены: {", ".join(allowed_statuses)}'
            )
        return value
    
    def update(self, instance, validated_data):
        """Обновление статуса с логикой начисления XP"""
        old_status = instance.status
        new_status = validated_data.get('status')
        instance = super().update(instance, validated_data)
        
        # Если статус изменен на 'completed' и XP еще не начислен
        if (old_status != 'completed' and new_status == 'completed' and 
            not instance.xp_awarded):
            from events.models import apply_event_completion_rewards
            apply_event_completion_rewards(instance)
            instance.xp_awarded = True
            instance.save(update_fields=['xp_awarded'])
        
        return instance
