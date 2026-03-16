"""
Контроллер для управления чатом.
"""
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.utils import timezone

from events.models import (
    ChatChannel, ChatChannelMembership, ChatMessage, 
    Event, Notification
)
from events.forms import ChatChannelForm, ChatMessageForm
from events.selectors import (
    available_channels_for_user,
    unread_message_counts_by_channel
)
from events.services import add_approved_volunteers_to_channel


class ChatController:
    """Контроллер для операций с чатом"""
    
    @staticmethod
    def get_user_channels(request):
        """Получает список доступных каналов чата для пользователя"""
        if not hasattr(request.user, 'profile'):
            raise ValueError('Профиль не найден.')
        
        channels = available_channels_for_user(request.user)
        return channels
    
    @staticmethod
    def get_channel_detail(request, channel_id):
        """Получает детали канала и сообщения"""
        if not hasattr(request.user, 'profile'):
            raise ValueError('Профиль не найден.')
        
        channel = get_object_or_404(
            ChatChannel.objects.select_related('event'),
            pk=channel_id,
            is_archived=False
        )
        
        channels_qs = available_channels_for_user(request.user)
        if not channels_qs.filter(pk=channel.pk).exists():
            raise ValueError('У вас нет доступа к этому каналу.')
        
        channels = list(channels_qs)
        
        # Создаем или получаем членство
        membership, _ = ChatChannelMembership.objects.get_or_create(
            channel=channel,
            user=request.user
        )
        
        # Получаем сообщения
        messages_qs = channel.messages.select_related('author__profile')
        
        # Обновляем last_read_at
        membership.last_read_at = timezone.now()
        membership.save(update_fields=['last_read_at'])
        
        # Получаем счетчики непрочитанных сообщений
        unread_by_channel = unread_message_counts_by_channel(request.user, channels)
        
        sidebar_channels = [
            {
                'channel': sidebar_channel,
                'unread': unread_by_channel.get(sidebar_channel.pk, 0),
            }
            for sidebar_channel in channels
        ]
        
        return {
            'channel': channel,
            'channels': channels,
            'sidebar_channels': sidebar_channels,
            'messages': messages_qs,
            'message_form': ChatMessageForm(),
        }
    
    @staticmethod
    @transaction.atomic
    def send_message(request, channel_id):
        """Отправляет сообщение в канал"""
        channel = get_object_or_404(ChatChannel, pk=channel_id, is_archived=False)
        
        # Проверяем доступ
        channels_qs = available_channels_for_user(request.user)
        if not channels_qs.filter(pk=channel.pk).exists():
            raise ValueError('У вас нет доступа к этому каналу.')
        
        form = ChatMessageForm(request.POST)
        if not form.is_valid():
            raise ValueError('Форма сообщения невалидна')
        
        message_obj = form.save(commit=False)
        message_obj.channel = channel
        message_obj.author = request.user
        message_obj.save()
        
        # Обновляем время последнего сообщения в канале
        channel.updated_at = timezone.now()
        channel.save(update_fields=['updated_at'])
        
        # Отправляем уведомления участникам канала
        recipients = ChatChannelMembership.objects.filter(
            channel=channel,
            notifications_enabled=True,
        ).exclude(user=request.user).values_list('user_id', flat=True)
        
        recipient_ids = list(recipients)
        if recipient_ids:
            preview = message_obj.content[:80]
            sender_name = request.user.get_full_name() or request.user.username
            notifications = [
                Notification(
                    user_id=user_id,
                    type='new_message',
                    title=f'Новое сообщение в канале "{channel.name}"',
                    message=f'{sender_name}: {preview}',
                    related_event=channel.event,
                )
                for user_id in recipient_ids
            ]
            Notification.objects.bulk_create(notifications)
        
        return message_obj
    
    @staticmethod
    @transaction.atomic
    def create_channel(request, event_pk):
        """Создает новый канал чата для события"""
        event = get_object_or_404(Event, pk=event_pk)
        
        if not hasattr(request.user, 'profile') or event.organizer != request.user:
            raise ValueError('Только организатор события может создавать каналы.')
        
        form = ChatChannelForm(request.POST)
        if not form.is_valid():
            raise ValueError('Форма канала невалидна')
        
        channel = form.save(commit=False)
        channel.event = event
        channel.created_by = request.user
        
        try:
            with transaction.atomic():
                channel.save()
                form.save_m2m()
        except IntegrityError:
            raise ValueError('Канал с таким названием для этого события уже существует.')
        
        # Добавляем создателя в канал
        ChatChannelMembership.objects.get_or_create(channel=channel, user=request.user)
        
        # Добавляем одобренных волонтеров в канал
        add_approved_volunteers_to_channel(channel, event)
        
        return channel
