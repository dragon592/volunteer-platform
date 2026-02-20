from datetime import date

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db.models import Count, F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import (
    ChatChannelForm,
    ChatMessageForm,
    EventForm,
    EventRegistrationForm,
    UserProfileForm,
    UserRegisterForm,
    VolunteerSearchForm,
)
from .models import (
    ChatChannel,
    ChatChannelMembership,
    ChatMessage,
    Event,
    EventRegistration,
    Notification,
    Skill,
    UserProfile,
    VolunteerAchievement,
    apply_event_completion_rewards,
)


def _events_base_queryset():
    return (
        Event.objects.filter(is_active=True)
        .select_related('organizer', 'organizer__profile')
        .prefetch_related('required_skills')
        .annotate(
            approved_participants=Count(
                'registrations',
                filter=Q(registrations__status__in=['approved', 'completed']),
            )
        )
    )


def _user_can_access_event_chat(user, event):
    if not user.is_authenticated:
        return False
    if event.organizer_id == user.id:
        return True
    return EventRegistration.objects.filter(
        event=event,
        volunteer=user,
        status__in=['approved', 'completed'],
    ).exists()


def _available_channels_for_user(user):
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
            | Q(event__registrations__volunteer=user, event__registrations__status__in=['approved', 'completed']),
            is_archived=False,
        )
        .select_related('event')
        .distinct()
        .order_by('-updated_at')
    )


def _add_volunteer_to_event_channels(user, event):
    for channel in event.chat_channels.all():
        ChatChannelMembership.objects.get_or_create(channel=channel, user=user)


def event_list(request):
    today = date.today()
    tab = request.GET.get('tab', 'current')
    events = _events_base_queryset()

    if tab == 'archive':
        events = events.filter(date__lt=today)
    else:
        tab = 'current'
        events = events.filter(date__gte=today)

    skill_id = request.GET.get('skill')
    city = request.GET.get('city')
    search = request.GET.get('search')
    event_type = request.GET.get('event_type')
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    participant = request.GET.get('participant')

    if skill_id:
        events = events.filter(required_skills__id=skill_id)
    if city:
        events = events.filter(city__icontains=city)
    if search:
        events = events.filter(Q(title__icontains=search) | Q(description__icontains=search))
    if event_type:
        events = events.filter(event_type=event_type)
    if date_from:
        events = events.filter(date__gte=date_from)
    if date_to:
        events = events.filter(date__lte=date_to)
    if status == 'open':
        events = events.filter(approved_participants__lt=F('max_volunteers'))
    elif status == 'full':
        events = events.filter(approved_participants__gte=F('max_volunteers'))
    elif status == 'mine' and request.user.is_authenticated:
        events = events.filter(
            Q(organizer=request.user) | Q(registrations__volunteer=request.user)
        )
    if participant:
        events = events.filter(
            Q(registrations__volunteer__username__icontains=participant)
            | Q(registrations__volunteer__first_name__icontains=participant)
            | Q(registrations__volunteer__last_name__icontains=participant)
        )

    events = events.distinct().order_by('date', 'time')
    skills = Skill.objects.all()
    cities = Event.objects.values_list('city', flat=True).distinct().exclude(city='')

    context = {
        'events': events,
        'skills': skills,
        'cities': cities,
        'event_type_choices': Event.TYPE_CHOICES,
        'tab': tab,
        'selected_skill': skill_id,
        'selected_city': city,
        'search_query': search,
        'selected_type': event_type,
        'selected_status': status,
        'selected_date_from': date_from,
        'selected_date_to': date_to,
        'selected_participant': participant,
    }
    return render(request, 'events/event_list.html', context)


def event_detail(request, pk):
    event = get_object_or_404(Event.objects.select_related('organizer__profile'), pk=pk)
    user_registration = None
    can_register = False
    can_open_chat = False

    if request.user.is_authenticated:
        user_registration = EventRegistration.objects.filter(event=event, volunteer=request.user).first()
        active_registration_exists = EventRegistration.objects.filter(
            event=event,
            volunteer=request.user,
            status__in=['pending', 'approved', 'completed'],
        ).exists()
        can_register = (
            request.user.profile.is_volunteer
            and not event.is_full
            and not active_registration_exists
            and event.date >= date.today()
        )
        can_open_chat = _user_can_access_event_chat(request.user, event)

    registrations = event.registrations.select_related('volunteer__profile')
    context = {
        'event': event,
        'user_registration': user_registration,
        'can_register': can_register,
        'registrations': registrations,
        'can_open_chat': can_open_chat,
        'event_chat_channel': event.chat_channels.first(),
    }
    return render(request, 'events/event_detail.html', context)


@login_required
def event_register(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if not request.user.profile.is_volunteer:
        messages.error(request, 'РўРѕР»СЊРєРѕ РІРѕР»РѕРЅС‚РµСЂС‹ РјРѕРіСѓС‚ Р·Р°РїРёСЃС‹РІР°С‚СЊСЃСЏ РЅР° СЃРѕР±С‹С‚РёСЏ.')
        return redirect('event_detail', pk=pk)

    if event.is_full:
        messages.error(request, 'Рљ СЃРѕР¶Р°Р»РµРЅРёСЋ, РІСЃРµ РјРµСЃС‚Р° Р·Р°РЅСЏС‚С‹.')
        return redirect('event_detail', pk=pk)

    existing = EventRegistration.objects.filter(event=event, volunteer=request.user).first()
    if existing and existing.status in ['pending', 'approved', 'completed']:
        messages.info(request, 'Р’С‹ СѓР¶Рµ Р·Р°РїРёСЃР°РЅС‹ РЅР° СЌС‚Рѕ СЃРѕР±С‹С‚РёРµ.')
        return redirect('event_detail', pk=pk)

    if request.method == 'POST':
        form = EventRegistrationForm(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.event = event
            registration.volunteer = request.user
            registration.save()
            messages.success(request, 'Р’С‹ СѓСЃРїРµС€РЅРѕ Р·Р°РїРёСЃР°Р»РёСЃСЊ РЅР° СЃРѕР±С‹С‚РёРµ!')
            Notification.objects.create(
                user=event.organizer,
                type='new_application',
                title='РќРѕРІР°СЏ Р·Р°СЏРІРєР° РЅР° СЃРѕР±С‹С‚РёРµ',
                message=f'{request.user.get_full_name()} РїРѕРґР°Р» Р·Р°СЏРІРєСѓ РЅР° СЃРѕР±С‹С‚РёРµ "{event.title}".',
                related_event=event,
                related_registration=registration,
            )
            return redirect('event_detail', pk=pk)
    else:
        form = EventRegistrationForm()

    return render(request, 'events/event_register.html', {'event': event, 'form': form})


@login_required
def event_cancel_registration(request, pk):
    event = get_object_or_404(Event, pk=pk)
    registration = get_object_or_404(EventRegistration, event=event, volunteer=request.user)
    if registration.status in ['completed', 'rejected']:
        messages.error(request, 'Р­С‚Сѓ Р·Р°СЏРІРєСѓ РЅРµР»СЊР·СЏ РѕС‚РјРµРЅРёС‚СЊ.')
        return redirect('event_detail', pk=pk)
    registration.status = 'cancelled'
    registration.save(update_fields=['status', 'updated_at'])
    messages.success(request, 'Р—Р°РїРёСЃСЊ РѕС‚РјРµРЅРµРЅР°.')
    return redirect('event_detail', pk=pk)


@login_required
def event_create(request):
    if not request.user.profile.is_organizer:
        messages.error(request, 'РўРѕР»СЊРєРѕ РѕСЂРіР°РЅРёР·Р°С‚РѕСЂС‹ РјРѕРіСѓС‚ СЃРѕР·РґР°РІР°С‚СЊ СЃРѕР±С‹С‚РёСЏ.')
        return redirect('event_list')

    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            form.save_m2m()
            messages.success(request, 'РЎРѕР±С‹С‚РёРµ СѓСЃРїРµС€РЅРѕ СЃРѕР·РґР°РЅРѕ!')
            return redirect('event_detail', pk=event.pk)
    else:
        form = EventForm()

    return render(request, 'events/event_form.html', {'form': form, 'title': 'РЎРѕР·РґР°С‚СЊ СЃРѕР±С‹С‚РёРµ'})


@login_required
def event_edit(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if event.organizer != request.user:
        messages.error(request, 'Р’С‹ РјРѕР¶РµС‚Рµ СЂРµРґР°РєС‚РёСЂРѕРІР°С‚СЊ С‚РѕР»СЊРєРѕ СЃРІРѕРё СЃРѕР±С‹С‚РёСЏ.')
        return redirect('event_detail', pk=pk)

    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'РЎРѕР±С‹С‚РёРµ РѕР±РЅРѕРІР»РµРЅРѕ!')
            return redirect('event_detail', pk=pk)
    else:
        form = EventForm(instance=event)

    return render(request, 'events/event_form.html', {'form': form, 'title': 'Р РµРґР°РєС‚РёСЂРѕРІР°С‚СЊ СЃРѕР±С‹С‚РёРµ', 'event': event})


@login_required
def event_manage_registrations(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if event.organizer != request.user:
        messages.error(request, 'Р’С‹ РјРѕР¶РµС‚Рµ СѓРїСЂР°РІР»СЏС‚СЊ С‚РѕР»СЊРєРѕ СЃРІРѕРёРјРё СЃРѕР±С‹С‚РёСЏРјРё.')
        return redirect('event_detail', pk=pk)

    if request.method == 'POST':
        reg_id = request.POST.get('registration_id')
        action = request.POST.get('action')
        registration = get_object_or_404(EventRegistration, pk=reg_id, event=event)

        if action == 'approve':
            registration.status = 'approved'
            registration.save(update_fields=['status', 'updated_at'])
            _add_volunteer_to_event_channels(registration.volunteer, event)
            messages.success(request, f'Р—Р°СЏРІРєР° {registration.volunteer.get_full_name()} РѕРґРѕР±СЂРµРЅР°.')
            Notification.objects.create(
                user=registration.volunteer,
                type='application_approved',
                title='Р—Р°СЏРІРєР° РѕРґРѕР±СЂРµРЅР°!',
                message=f'Р’Р°С€Р° Р·Р°СЏРІРєР° РЅР° СЃРѕР±С‹С‚РёРµ "{event.title}" Р±С‹Р»Р° РѕРґРѕР±СЂРµРЅР°.',
                related_event=event,
                related_registration=registration,
            )
        elif action == 'reject':
            registration.status = 'rejected'
            registration.save(update_fields=['status', 'updated_at'])
            messages.success(request, f'Р—Р°СЏРІРєР° {registration.volunteer.get_full_name()} РѕС‚РєР»РѕРЅРµРЅР°.')
            Notification.objects.create(
                user=registration.volunteer,
                type='application_rejected',
                title='Р—Р°СЏРІРєР° РѕС‚РєР»РѕРЅРµРЅР°',
                message=f'Рљ СЃРѕР¶Р°Р»РµРЅРёСЋ, РІР°С€Р° Р·Р°СЏРІРєР° РЅР° СЃРѕР±С‹С‚РёРµ "{event.title}" Р±С‹Р»Р° РѕС‚РєР»РѕРЅРµРЅР°.',
                related_event=event,
                related_registration=registration,
            )
        elif action == 'complete':
            if event.date > date.today():
                messages.error(request, 'РќРµР»СЊР·СЏ Р·Р°РІРµСЂС€РёС‚СЊ СѓС‡Р°СЃС‚РёРµ РґРѕ РґР°С‚С‹ СЃРѕР±С‹С‚РёСЏ.')
            elif registration.status not in ['approved', 'completed']:
                messages.error(request, 'Р—Р°РІРµСЂС€РёС‚СЊ РјРѕР¶РЅРѕ С‚РѕР»СЊРєРѕ РѕРґРѕР±СЂРµРЅРЅРѕРіРѕ СѓС‡Р°СЃС‚РЅРёРєР°.')
            else:
                registration.status = 'completed'
                registration.completed_at = timezone.now()
                registration.save(update_fields=['status', 'completed_at', 'updated_at'])
                apply_event_completion_rewards(registration)
                messages.success(
                    request,
                    f'РЈС‡Р°СЃС‚РёРµ {registration.volunteer.get_full_name()} Р·Р°РІРµСЂС€РµРЅРѕ, XP Рё РґРѕСЃС‚РёР¶РµРЅРёСЏ РѕР±РЅРѕРІР»РµРЅС‹.',
                )

    registrations = event.registrations.select_related('volunteer__profile')
    return render(request, 'events/event_manage.html', {'event': event, 'registrations': registrations})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('event_list')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Р”РѕР±СЂРѕ РїРѕР¶Р°Р»РѕРІР°С‚СЊ! Р’Р°С€ Р°РєРєР°СѓРЅС‚ СЃРѕР·РґР°РЅ.')
            return redirect('profile')
    else:
        form = UserRegisterForm()

    return render(request, 'events/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('event_list')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Р”РѕР±СЂРѕ РїРѕР¶Р°Р»РѕРІР°С‚СЊ, {user.get_full_name() or user.username}!')
            next_url = request.GET.get('next', 'event_list')
            return redirect(next_url)
    else:
        form = AuthenticationForm()

    return render(request, 'events/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'Р’С‹ РІС‹С€Р»Рё РёР· СЃРёСЃС‚РµРјС‹.')
    return redirect('event_list')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'РџСЂРѕС„РёР»СЊ РѕР±РЅРѕРІР»РµРЅ!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user.profile, user=request.user)

    if request.user.profile.is_organizer:
        my_events = Event.objects.filter(organizer=request.user)
        achievements = None
    else:
        my_events = Event.objects.filter(
            registrations__volunteer=request.user,
            registrations__status__in=['pending', 'approved', 'completed'],
        )
        achievements = (
            VolunteerAchievement.objects.filter(volunteer=request.user)
            .select_related('achievement')
            .order_by('-awarded_at')
        )

    context = {
        'form': form,
        'my_events': my_events,
        'achievements': achievements,
        'xp_progress_percent': request.user.profile.xp % 100,
    }
    return render(request, 'events/profile.html', context)


@login_required
def my_events(request):
    if request.user.profile.is_organizer:
        events = Event.objects.filter(organizer=request.user).annotate(registrations_count=Count('registrations'))
        registrations = None
    else:
        events = Event.objects.filter(registrations__volunteer=request.user).distinct()
        registrations = {
            r.event_id: r
            for r in EventRegistration.objects.filter(volunteer=request.user)
        }

    context = {
        'events': events,
        'registrations': registrations,
    }
    return render(request, 'events/my_events.html', context)


@login_required
def volunteer_search(request):
    if not request.user.profile.is_organizer:
        messages.error(request, 'РўРѕР»СЊРєРѕ РѕСЂРіР°РЅРёР·Р°С‚РѕСЂС‹ РјРѕРіСѓС‚ РёСЃРєР°С‚СЊ РІРѕР»РѕРЅС‚РµСЂРѕРІ.')
        return redirect('event_list')

    form = VolunteerSearchForm(request.GET or None)
    volunteers = UserProfile.objects.filter(role='volunteer').select_related('user')

    if form.is_valid():
        skills = form.cleaned_data.get('skills')
        city = form.cleaned_data.get('city')

        if skills:
            volunteers = volunteers.filter(skills__in=skills).distinct()
        if city:
            volunteers = volunteers.filter(city__icontains=city)

    volunteers = volunteers.prefetch_related('skills')

    context = {
        'form': form,
        'volunteers': volunteers,
    }
    return render(request, 'events/volunteer_search.html', context)


def volunteer_profile(request, pk):
    profile = get_object_or_404(UserProfile, pk=pk)

    completed_events = EventRegistration.objects.filter(
        volunteer=profile.user,
        status='completed',
    ).count()
    achievements = VolunteerAchievement.objects.filter(volunteer=profile.user).select_related('achievement')

    context = {
        'volunteer_profile': profile,
        'completed_events': completed_events,
        'achievements': achievements,
    }
    return render(request, 'events/volunteer_profile.html', context)


@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(user=request.user)
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)
    elif filter_type == 'read':
        notifications = notifications.filter(is_read=True)

    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    context = {
        'notifications': notifications,
        'unread_count': unread_count,
        'filter_type': filter_type,
    }
    return render(request, 'events/notifications.html', context)


@login_required
def notification_mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    return redirect('notifications_list')


@login_required
def notification_mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    messages.success(request, 'Р’СЃРµ СѓРІРµРґРѕРјР»РµРЅРёСЏ РѕС‚РјРµС‡РµРЅС‹ РєР°Рє РїСЂРѕС‡РёС‚Р°РЅРЅС‹Рµ')
    return redirect('notifications_list')


@login_required
def notifications_unread_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def notifications_latest(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:5]
    data = {
        'notifications': [
            {
                'id': n.id,
                'type': n.type,
                'title': n.title,
                'message': n.message,
                'icon': n.icon,
                'created_at': n.created_at.strftime('%d.%m.%Y %H:%M'),
                'url': reverse('event_detail', kwargs={'pk': n.related_event.pk}) if n.related_event else None,
            }
            for n in notifications
        ],
        'count': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    return JsonResponse(data)


@login_required
def chat_channels(request):
    channels = _available_channels_for_user(request.user)
    return render(request, 'events/chat_channels.html', {'channels': channels})


@login_required
def chat_channel_detail(request, channel_id):
    channel = get_object_or_404(ChatChannel.objects.select_related('event'), pk=channel_id, is_archived=False)
    channels = _available_channels_for_user(request.user)
    if not channels.filter(pk=channel.pk).exists():
        messages.error(request, 'РЈ РІР°СЃ РЅРµС‚ РґРѕСЃС‚СѓРїР° Рє СЌС‚РѕРјСѓ РєР°РЅР°Р»Сѓ.')
        return redirect('chat_channels')

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
            ).exclude(user=request.user)

            for recipient in recipients.select_related('user'):
                Notification.objects.create(
                    user=recipient.user,
                    type='new_message',
                    title=f'РќРѕРІРѕРµ СЃРѕРѕР±С‰РµРЅРёРµ РІ РєР°РЅР°Р»Рµ "{channel.name}"',
                    message=f'{request.user.get_full_name() or request.user.username}: {message_obj.content[:80]}',
                    related_event=channel.event,
                )
            return redirect('chat_channel_detail', channel_id=channel.pk)
    else:
        form = ChatMessageForm()

    messages_qs = channel.messages.select_related('author__profile')
    membership.last_read_at = timezone.now()
    membership.save(update_fields=['last_read_at'])

    memberships = {
        m.channel_id: m
        for m in ChatChannelMembership.objects.filter(channel__in=channels, user=request.user)
    }
    unread_by_channel = {}
    for sidebar_channel in channels:
        sidebar_membership = memberships.get(sidebar_channel.pk)
        if not sidebar_membership:
            unread_by_channel[sidebar_channel.pk] = 0
            continue
        unread_by_channel[sidebar_channel.pk] = ChatMessage.objects.filter(
            channel=sidebar_channel,
            created_at__gt=sidebar_membership.last_read_at,
        ).exclude(author=request.user).count()

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
    if event.organizer != request.user:
        messages.error(request, 'РўРѕР»СЊРєРѕ РѕСЂРіР°РЅРёР·Р°С‚РѕСЂ СЃРѕР±С‹С‚РёСЏ РјРѕР¶РµС‚ СЃРѕР·РґР°РІР°С‚СЊ РєР°РЅР°Р»С‹.')
        return redirect('event_detail', pk=event.pk)

    if request.method == 'POST':
        form = ChatChannelForm(request.POST)
        if form.is_valid():
            channel = form.save(commit=False)
            channel.event = event
            channel.created_by = request.user
            channel.save()

            ChatChannelMembership.objects.get_or_create(channel=channel, user=request.user)
            approved_volunteers = User.objects.filter(
                event_registrations__event=event,
                event_registrations__status__in=['approved', 'completed'],
            ).distinct()
            for volunteer in approved_volunteers:
                ChatChannelMembership.objects.get_or_create(channel=channel, user=volunteer)

            messages.success(request, 'РљР°РЅР°Р» СѓСЃРїРµС€РЅРѕ СЃРѕР·РґР°РЅ.')
            return redirect('chat_channel_detail', channel_id=channel.pk)
    else:
        form = ChatChannelForm()

    return render(request, 'events/chat_channel_form.html', {'event': event, 'form': form})
