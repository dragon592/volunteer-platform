from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ChatChannelForm, ChatMessageForm
from .models import ChatChannel, ChatChannelMembership, Event, Notification
from .selectors import available_channels_for_user, unread_message_counts_by_channel
from .services import add_approved_volunteers_to_channel
from .controllers.chat_controller import ChatController


@login_required
def chat_channels(request):
    """Список каналов чата"""
    try:
        channels = ChatController.get_user_channels(request)
        return render(request, 'events/chat_channels.html', {'channels': channels})
    except Exception as e:
        messages.error(request, f'Ошибка загрузки каналов: {str(e)}')
        return redirect('event_list')


@login_required
def chat_channel_detail(request, channel_id):
    """Детали канала чата и сообщения"""
    try:
        context = ChatController.get_channel_detail(request, channel_id)
        return render(request, 'events/chat_channel_detail.html', context)
    except Exception as e:
        messages.error(request, f'Ошибка загрузки канала: {str(e)}')
        return redirect('chat_channels')


@login_required
def chat_create_channel(request, event_pk):
    """Создание нового канала чата для события"""
    try:
        if request.method == 'POST':
            channel = ChatController.create_channel(request, event_pk)
            messages.success(request, 'Канал успешно создан.')
            return redirect('chat_channel_detail', channel_id=channel.pk)
        else:
            event = get_object_or_404(Event, pk=event_pk)
            form = ChatChannelForm()
        
        return render(request, 'events/chat_channel_form.html', {'event': event, 'form': form})
    except Exception as e:
        messages.error(request, f'Ошибка создания канала: {str(e)}')
        return redirect('event_detail', pk=event_pk)
