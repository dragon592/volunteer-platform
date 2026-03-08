from django.db.models import Count, Q

from .constants import APPROVED_REGISTRATION_STATUSES
from .models import ChatChannel, ChatChannelMembership, ChatMessage, Event, EventRegistration


def events_base_queryset():
    return (
        Event.objects.filter(is_active=True)
        .select_related('organizer', 'organizer__profile')
        .prefetch_related('required_skills')
        .annotate(
            approved_participants=Count(
                'registrations',
                filter=Q(registrations__status__in=APPROVED_REGISTRATION_STATUSES),
            )
        )
    )


def user_can_access_event_chat(user, event):
    if not user.is_authenticated:
        return False
    if event.organizer_id == user.id:
        return True
    return EventRegistration.objects.filter(
        event=event,
        volunteer=user,
        status__in=APPROVED_REGISTRATION_STATUSES,
    ).exists()


def available_channels_for_user(user):
    if not user.is_authenticated:
        return ChatChannel.objects.none()

    if user.profile.is_organizer:
        return (
            ChatChannel.objects.filter(
                Q(event__organizer=user) | Q(memberships__user=user),
                is_archived=False,
            )
            .select_related('event')
            .distinct()
            .order_by('-updated_at')
        )

    return (
        ChatChannel.objects.filter(
            Q(memberships__user=user)
            | Q(
                event__registrations__volunteer=user,
                event__registrations__status__in=APPROVED_REGISTRATION_STATUSES,
            ),
            is_archived=False,
        )
        .select_related('event')
        .distinct()
        .order_by('-updated_at')
    )


def unread_message_counts_by_channel(user, channels):
    memberships = list(
        ChatChannelMembership.objects.filter(channel__in=channels, user=user)
        .values('channel_id', 'last_read_at')
    )
    unread_by_channel = {item['channel_id']: 0 for item in memberships}

    unread_filter = Q()
    for item in memberships:
        unread_filter |= Q(channel_id=item['channel_id'], created_at__gt=item['last_read_at'])

    if unread_filter:
        unread_counts = (
            ChatMessage.objects.filter(unread_filter)
            .exclude(author=user)
            .values('channel_id')
            .annotate(total=Count('id'))
        )
        unread_by_channel.update({item['channel_id']: item['total'] for item in unread_counts})

    return unread_by_channel
