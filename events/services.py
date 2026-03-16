from django.db import IntegrityError
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .constants import REAPPLY_REGISTRATION_STATUSES
from .models import ChatChannelMembership, EventRegistration, Notification, User


def safe_redirect_target(request, fallback='event_list'):
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return reverse(fallback)


def add_volunteer_to_event_channels(user, event):
    for channel in event.chat_channels.all():
        ChatChannelMembership.objects.get_or_create(channel=channel, user=user)


def remove_volunteer_from_event_channels(user, event):
    ChatChannelMembership.objects.filter(channel__event=event, user=user).delete()


def submit_event_registration(form, event, volunteer, existing_registration=None):
    """
    Обрабатывает заявку на участие в событии.
    Поддерживает повторную подачу заявки при статусе 'rejected' или 'cancelled'.
    """
    should_notify_organizer = True

    # Если есть существующая заявка в статусе для повторной подачи
    if existing_registration and existing_registration.status in REAPPLY_REGISTRATION_STATUSES:
        registration = existing_registration
        registration.status = 'pending'
        registration.message = form.cleaned_data['message']
        registration.completed_at = None
        registration.save(update_fields=['status', 'message', 'completed_at', 'updated_at'])
        remove_volunteer_from_event_channels(volunteer, event)
        success_message = 'Заявка отправлена повторно.'
    else:
        try:
            # Пытаемся создать новую заявку
            registration = form.save(commit=False)
            registration.event = event
            registration.volunteer = volunteer
            registration.save()
            success_message = 'Вы успешно записались на событие!'
        except IntegrityError:
            # Заявка уже существует
            registration = EventRegistration.objects.get(event=event, volunteer=volunteer)
            if registration.status in REAPPLY_REGISTRATION_STATUSES:
                # Повторная подача
                registration.status = 'pending'
                registration.message = form.cleaned_data['message']
                registration.completed_at = None
                registration.save(update_fields=['status', 'message', 'completed_at', 'updated_at'])
                remove_volunteer_from_event_channels(volunteer, event)
                success_message = 'Заявка отправлена повторно.'
            else:
                # Заявка уже есть в активном статусе
                should_notify_organizer = False
                success_message = 'Вы уже записаны на это событие.'

    # Отправляем уведомления
    if should_notify_organizer:
        Notification.objects.create(
            user=event.organizer,
            type='new_application',
            title='Новая заявка на событие',
            message=f'{volunteer.get_full_name()} подал заявку на событие "{event.title}".',
            related_event=event,
            related_registration=registration,
        )
        Notification.objects.create(
            user=volunteer,
            type='new_application',
            title='Заявка отправлена',
            message=f'Ваша заявка на событие "{event.title}" была отправлена организатору.',
            related_event=event,
            related_registration=registration,
        )
    return registration, success_message


def notify_registration_approved(registration, event):
    Notification.objects.create(
        user=registration.volunteer,
        type='application_approved',
        title='Заявка одобрена!',
        message=f'Ваша заявка на событие "{event.title}" была одобрена.',
        related_event=event,
        related_registration=registration,
    )


def notify_registration_rejected(registration, event):
    Notification.objects.create(
        user=registration.volunteer,
        type='application_rejected',
        title='Заявка отклонена',
        message=f'К сожалению, ваша заявка на событие "{event.title}" была отклонена.',
        related_event=event,
        related_registration=registration,
    )


def add_approved_volunteers_to_channel(channel, event):
    approved_volunteers = (
        EventRegistration.objects.filter(
            event=event,
            status__in=['approved', 'completed'],
        )
        .select_related('volunteer')
        .distinct()
    )
    for registration in approved_volunteers:
        ChatChannelMembership.objects.get_or_create(channel=channel, user=registration.volunteer)


def notify_event_created(event, exclude_user=None):
    """Отправляет уведомления волонтерам о создании нового события"""
    volunteers = User.objects.filter(profile__role='volunteer')
    if exclude_user:
        volunteers = volunteers.exclude(id=exclude_user.id)
    
    notifications = [
        Notification(
            user=volunteer,
            type='new_event',
            title='Новое событие!',
            message=f'Появилось новое событие: "{event.title}"',
            related_event=event,
        )
        for volunteer in volunteers
    ]
    Notification.objects.bulk_create(notifications, ignore_conflicts=True)


def notify_event_updated(event, participants=None):
    """Отправляет уведомления участникам события об его обновлении"""
    if participants is None:
        participants = User.objects.filter(
            event_registrations__event=event,
            event_registrations__status__in=['approved', 'completed']
        ).distinct()
    
    notifications = [
        Notification(
            user=participant,
            type='new_event',  # TODO: Создать отдельный тип 'event_updated' в модели Notification
            title='Событие обновлено',
            message=f'Событие "{event.title}" было обновлено организатором.',
            related_event=event,
        )
        for participant in participants
    ]
    Notification.objects.bulk_create(notifications, ignore_conflicts=True)
