from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ChatChannelForm, ChatMessageForm
from .models import ChatChannel, ChatChannelMembership, Event, Notification
from .selectors import available_channels_for_user, unread_message_counts_by_channel
from .services import add_approved_volunteers_to_channel


@login_required
def chat_channels(request):
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Профиль не найден.')
        return redirect('event_list')
    channels = available_channels_for_user(request.user)
    return render(request, 'events/chat_channels.html', {'channels': channels})


@login_required
def chat_channel_detail(request, channel_id):
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Профиль не найден.')
        return redirect('event_list')
    channel = get_object_or_404(ChatChannel.objects.select_related('event'), pk=channel_id, is_archived=False)
    channels_qs = available_channels_for_user(request.user)
    if not channels_qs.filter(pk=channel.pk).exists():
        messages.error(request, 'У вас нет доступа к этому каналу.')
        return redirect('chat_channels')
    channels = list(channels_qs)

    membership, _ = ChatChannelMembership.objects.get_or_create(channel=channel, user=request.user)

    if request.method == 'POST':
        form = ChatMessageForm(request.POST)
        if form.is_valid():
            message_obj = form.save(commit=False)
            message_obj.channel = channel
            message_obj.author = request.user
            message_obj.save()
            channel.updated_at = timezone.now()
            channel.save(update_fields=['updated_at'])

            recipients = ChatChannelMembership.objects.filter(
                channel=channel,
                notifications_enabled=True,
            ).exclude(user=request.user).values_list('user_id', flat=True)

            recipient_ids = list(recipients)
            if recipient_ids:
                preview = message_obj.content[:80]
                sender_name = request.user.get_full_name() or request.user.username
                Notification.objects.bulk_create(
                    [
                        Notification(
                            user_id=user_id,
                            type='new_message',
                            title=f'Новое сообщение в канале "{channel.name}"',
                            message=f'{sender_name}: {preview}',
                            related_event=channel.event,
                        )
                        for user_id in recipient_ids
                    ]
                )
            return redirect('chat_channel_detail', channel_id=channel.pk)
    else:
        form = ChatMessageForm()

    messages_qs = channel.messages.select_related('author__profile')
    membership.last_read_at = timezone.now()
    membership.save(update_fields=['last_read_at'])

    unread_by_channel = unread_message_counts_by_channel(request.user, channels)

    sidebar_channels = [
        {
            'channel': sidebar_channel,
            'unread': unread_by_channel.get(sidebar_channel.pk, 0),
        }
        for sidebar_channel in channels
    ]

    context = {
        'channels': channels,
        'sidebar_channels': sidebar_channels,
        'channel': channel,
        'messages': messages_qs,
        'message_form': form,
    }
    return render(request, 'events/chat_channel_detail.html', context)


@login_required
def chat_create_channel(request, event_pk):
    event = get_object_or_404(Event, pk=event_pk)
    if not hasattr(request.user, 'profile') or event.organizer != request.user:
        messages.error(request, 'Только организатор события может создавать каналы.')
        return redirect('event_detail', pk=event.pk)

    if request.method == 'POST':
        form = ChatChannelForm(request.POST)
        if form.is_valid():
            channel = form.save(commit=False)
            channel.event = event
            channel.created_by = request.user
            try:
                with transaction.atomic():
                    channel.save()
            except IntegrityError:
                form.add_error('name', 'Канал с таким названием для этого события уже существует.')
                channel = None

            if channel is not None:
                ChatChannelMembership.objects.get_or_create(channel=channel, user=request.user)
                add_approved_volunteers_to_channel(channel, event)
                messages.success(request, 'Канал успешно создан.')
                return redirect('chat_channel_detail', channel_id=channel.pk)
    else:
        form = ChatChannelForm()

    return render(request, 'events/chat_channel_form.html', {'event': event, 'form': form})
