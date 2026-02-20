<<<<<<< HEAD
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

=======
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse
from datetime import date
import json

from .models import Event, EventRegistration, UserProfile, Skill, Notification
from .forms import (
    UserRegisterForm, UserProfileForm, EventForm, 
    EventRegistrationForm, VolunteerSearchForm
)


def event_list(request):
    """Главная страница - список событий"""
    events = Event.objects.filter(is_active=True, date__gte=date.today())
    
    # Фильтрация
    skill_id = request.GET.get('skill')
    city = request.GET.get('city')
    search = request.GET.get('search')
    
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    if skill_id:
        events = events.filter(required_skills__id=skill_id)
    if city:
        events = events.filter(city__icontains=city)
    if search:
<<<<<<< HEAD
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

=======
        events = events.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )
    
    events = events.distinct().order_by('date')
    skills = Skill.objects.all()
    cities = Event.objects.values_list('city', flat=True).distinct().exclude(city='')
    
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    context = {
        'events': events,
        'skills': skills,
        'cities': cities,
<<<<<<< HEAD
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
=======
        'selected_skill': skill_id,
        'selected_city': city,
        'search_query': search,
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    }
    return render(request, 'events/event_list.html', context)


def event_detail(request, pk):
<<<<<<< HEAD
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
=======
    """Детали события"""
    event = get_object_or_404(Event, pk=pk)
    user_registration = None
    can_register = False
    
    if request.user.is_authenticated:
        user_registration = EventRegistration.objects.filter(
            event=event, volunteer=request.user
        ).first()
        can_register = (
            request.user.profile.is_volunteer and 
            not event.is_full and 
            not user_registration and
            event.date >= date.today()
        )
    
    registrations = event.registrations.select_related('volunteer__profile')
    
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    context = {
        'event': event,
        'user_registration': user_registration,
        'can_register': can_register,
        'registrations': registrations,
<<<<<<< HEAD
        'can_open_chat': can_open_chat,
        'event_chat_channel': event.chat_channels.first(),
=======
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    }
    return render(request, 'events/event_detail.html', context)


@login_required
def event_register(request, pk):
<<<<<<< HEAD
    event = get_object_or_404(Event, pk=pk)

    if not request.user.profile.is_volunteer:
        messages.error(request, 'Только волонтеры могут записываться на события.')
        return redirect('event_detail', pk=pk)

    if event.is_full:
        messages.error(request, 'К сожалению, все места заняты.')
        return redirect('event_detail', pk=pk)

    existing = EventRegistration.objects.filter(event=event, volunteer=request.user).first()
    if existing and existing.status in ['pending', 'approved', 'completed']:
        messages.info(request, 'Вы уже записаны на это событие.')
        return redirect('event_detail', pk=pk)

=======
    """Запись на событие"""
    event = get_object_or_404(Event, pk=pk)
    
    if not request.user.profile.is_volunteer:
        messages.error(request, 'Только волонтёры могут записываться на события.')
        return redirect('event_detail', pk=pk)
    
    if event.is_full:
        messages.error(request, 'К сожалению, все места заняты.')
        return redirect('event_detail', pk=pk)
    
    existing = EventRegistration.objects.filter(event=event, volunteer=request.user).first()
    if existing:
        messages.info(request, 'Вы уже записаны на это событие.')
        return redirect('event_detail', pk=pk)
    
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    if request.method == 'POST':
        form = EventRegistrationForm(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.event = event
            registration.volunteer = request.user
            registration.save()
            messages.success(request, 'Вы успешно записались на событие!')
<<<<<<< HEAD
=======
            # Создаём уведомление для организатора
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
            Notification.objects.create(
                user=event.organizer,
                type='new_application',
                title='Новая заявка на событие',
                message=f'{request.user.get_full_name()} подал заявку на событие "{event.title}".',
                related_event=event,
<<<<<<< HEAD
                related_registration=registration,
=======
                related_registration=registration
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
            )
            return redirect('event_detail', pk=pk)
    else:
        form = EventRegistrationForm()
<<<<<<< HEAD

=======
    
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    return render(request, 'events/event_register.html', {'event': event, 'form': form})


@login_required
def event_cancel_registration(request, pk):
<<<<<<< HEAD
    event = get_object_or_404(Event, pk=pk)
    registration = get_object_or_404(EventRegistration, event=event, volunteer=request.user)
    if registration.status in ['completed', 'rejected']:
        messages.error(request, 'Эту заявку нельзя отменить.')
        return redirect('event_detail', pk=pk)
    registration.status = 'cancelled'
    registration.save(update_fields=['status', 'updated_at'])
=======
    """Отмена записи на событие"""
    event = get_object_or_404(Event, pk=pk)
    registration = get_object_or_404(
        EventRegistration, event=event, volunteer=request.user
    )
    registration.status = 'cancelled'
    registration.save()
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    messages.success(request, 'Запись отменена.')
    return redirect('event_detail', pk=pk)


@login_required
def event_create(request):
<<<<<<< HEAD
    if not request.user.profile.is_organizer:
        messages.error(request, 'Только организаторы могут создавать события.')
        return redirect('event_list')

=======
    """Создание события (только для организаторов)"""
    if not request.user.profile.is_organizer:
        messages.error(request, 'Только организаторы могут создавать события.')
        return redirect('event_list')
    
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            form.save_m2m()
            messages.success(request, 'Событие успешно создано!')
            return redirect('event_detail', pk=event.pk)
    else:
        form = EventForm()
<<<<<<< HEAD

=======
    
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    return render(request, 'events/event_form.html', {'form': form, 'title': 'Создать событие'})


@login_required
def event_edit(request, pk):
<<<<<<< HEAD
    event = get_object_or_404(Event, pk=pk)

    if event.organizer != request.user:
        messages.error(request, 'Вы можете редактировать только свои события.')
        return redirect('event_detail', pk=pk)

=======
    """Редактирование события"""
    event = get_object_or_404(Event, pk=pk)
    
    if event.organizer != request.user:
        messages.error(request, 'Вы можете редактировать только свои события.')
        return redirect('event_detail', pk=pk)
    
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Событие обновлено!')
            return redirect('event_detail', pk=pk)
    else:
        form = EventForm(instance=event)
<<<<<<< HEAD

=======
    
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    return render(request, 'events/event_form.html', {'form': form, 'title': 'Редактировать событие', 'event': event})


@login_required
def event_manage_registrations(request, pk):
<<<<<<< HEAD
    event = get_object_or_404(Event, pk=pk)

    if event.organizer != request.user:
        messages.error(request, 'Вы можете управлять только своими событиями.')
        return redirect('event_detail', pk=pk)

=======
    """Управление заявками на событие (для организатора)"""
    event = get_object_or_404(Event, pk=pk)
    
    if event.organizer != request.user:
        messages.error(request, 'Вы можете управлять только своими событиями.')
        return redirect('event_detail', pk=pk)
    
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    if request.method == 'POST':
        reg_id = request.POST.get('registration_id')
        action = request.POST.get('action')
        registration = get_object_or_404(EventRegistration, pk=reg_id, event=event)
<<<<<<< HEAD

        if action == 'approve':
            registration.status = 'approved'
            registration.save(update_fields=['status', 'updated_at'])
            _add_volunteer_to_event_channels(registration.volunteer, event)
            messages.success(request, f'Заявка {registration.volunteer.get_full_name()} одобрена.')
=======
        
        if action == 'approve':
            registration.status = 'approved'
            messages.success(request, f'Заявка {registration.volunteer.get_full_name()} одобрена.')
            # Создаём уведомление для волонтёра
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
            Notification.objects.create(
                user=registration.volunteer,
                type='application_approved',
                title='Заявка одобрена!',
                message=f'Ваша заявка на событие "{event.title}" была одобрена.',
                related_event=event,
<<<<<<< HEAD
                related_registration=registration,
            )
        elif action == 'reject':
            registration.status = 'rejected'
            registration.save(update_fields=['status', 'updated_at'])
            messages.success(request, f'Заявка {registration.volunteer.get_full_name()} отклонена.')
=======
                related_registration=registration
            )
        elif action == 'reject':
            registration.status = 'rejected'
            messages.success(request, f'Заявка {registration.volunteer.get_full_name()} отклонена.')
            # Создаём уведомление для волонтёра
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
            Notification.objects.create(
                user=registration.volunteer,
                type='application_rejected',
                title='Заявка отклонена',
                message=f'К сожалению, ваша заявка на событие "{event.title}" была отклонена.',
                related_event=event,
<<<<<<< HEAD
                related_registration=registration,
            )
        elif action == 'complete':
            if event.date > date.today():
                messages.error(request, 'Нельзя завершить участие до даты события.')
            elif registration.status not in ['approved', 'completed']:
                messages.error(request, 'Завершить можно только одобренного участника.')
            else:
                registration.status = 'completed'
                registration.completed_at = timezone.now()
                registration.save(update_fields=['status', 'completed_at', 'updated_at'])
                apply_event_completion_rewards(registration)
                messages.success(
                    request,
                    f'Участие {registration.volunteer.get_full_name()} завершено, XP и достижения обновлены.',
                )

=======
                related_registration=registration
            )
        registration.save()
    
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    registrations = event.registrations.select_related('volunteer__profile')
    return render(request, 'events/event_manage.html', {'event': event, 'registrations': registrations})


def register_view(request):
<<<<<<< HEAD
    if request.user.is_authenticated:
        return redirect('event_list')

=======
    """Регистрация нового пользователя"""
    if request.user.is_authenticated:
        return redirect('event_list')
    
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Добро пожаловать! Ваш аккаунт создан.')
            return redirect('profile')
    else:
        form = UserRegisterForm()
<<<<<<< HEAD

=======
    
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    return render(request, 'events/register.html', {'form': form})


def login_view(request):
<<<<<<< HEAD
    if request.user.is_authenticated:
        return redirect('event_list')

=======
    """Авторизация"""
    if request.user.is_authenticated:
        return redirect('event_list')
    
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.get_full_name() or user.username}!')
            next_url = request.GET.get('next', 'event_list')
            return redirect(next_url)
    else:
        form = AuthenticationForm()
<<<<<<< HEAD

=======
    
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    return render(request, 'events/login.html', {'form': form})


def logout_view(request):
<<<<<<< HEAD
=======
    """Выход"""
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    logout(request)
    messages.success(request, 'Вы вышли из системы.')
    return redirect('event_list')


@login_required
def profile_view(request):
<<<<<<< HEAD
=======
    """Просмотр и редактирование профиля"""
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile, user=request.user)
        if form.is_valid():
            form.save()
<<<<<<< HEAD
            messages.success(request, 'Профиль обновлен!')
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
=======
            messages.success(request, 'Профиль обновлён!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user.profile, user=request.user)
    
    # Получаем события пользователя
    if request.user.profile.is_organizer:
        my_events = Event.objects.filter(organizer=request.user)
    else:
        my_events = Event.objects.filter(
            registrations__volunteer=request.user,
            registrations__status__in=['pending', 'approved']
        )
    
    context = {
        'form': form,
        'my_events': my_events,
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    }
    return render(request, 'events/profile.html', context)


@login_required
def my_events(request):
<<<<<<< HEAD
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
=======
    """Мои события"""
    if request.user.profile.is_organizer:
        events = Event.objects.filter(organizer=request.user).annotate(
            registrations_count=Count('registrations')
        )
    else:
        events = Event.objects.filter(
            registrations__volunteer=request.user
        ).distinct()
        registrations = {
            r.event_id: r for r in EventRegistration.objects.filter(volunteer=request.user)
        }
    
    context = {
        'events': events,
        'registrations': registrations if not request.user.profile.is_organizer else None,
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    }
    return render(request, 'events/my_events.html', context)


@login_required
def volunteer_search(request):
<<<<<<< HEAD
    if not request.user.profile.is_organizer:
        messages.error(request, 'Только организаторы могут искать волонтеров.')
        return redirect('event_list')

    form = VolunteerSearchForm(request.GET or None)
    volunteers = UserProfile.objects.filter(role='volunteer').select_related('user')

    if form.is_valid():
        skills = form.cleaned_data.get('skills')
        city = form.cleaned_data.get('city')

=======
    """Поиск волонтёров (только для организаторов)"""
    if not request.user.profile.is_organizer:
        messages.error(request, 'Только организаторы могут искать волонтёров.')
        return redirect('event_list')
    
    form = VolunteerSearchForm(request.GET or None)
    volunteers = UserProfile.objects.filter(role='volunteer').select_related('user')
    
    if form.is_valid():
        skills = form.cleaned_data.get('skills')
        city = form.cleaned_data.get('city')
        
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
        if skills:
            volunteers = volunteers.filter(skills__in=skills).distinct()
        if city:
            volunteers = volunteers.filter(city__icontains=city)
<<<<<<< HEAD

    volunteers = volunteers.prefetch_related('skills')

=======
    
    volunteers = volunteers.prefetch_related('skills')
    
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    context = {
        'form': form,
        'volunteers': volunteers,
    }
    return render(request, 'events/volunteer_search.html', context)


def volunteer_profile(request, pk):
<<<<<<< HEAD
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
=======
    """Просмотр профиля волонтёра"""
    profile = get_object_or_404(UserProfile, pk=pk)
    
    # Статистика волонтёра
    completed_events = EventRegistration.objects.filter(
        volunteer=profile.user,
        status='approved',
        event__date__lt=date.today()
    ).count()
    
    context = {
        'volunteer_profile': profile,
        'completed_events': completed_events,
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    }
    return render(request, 'events/volunteer_profile.html', context)


@login_required
def notifications_list(request):
<<<<<<< HEAD
    notifications = Notification.objects.filter(user=request.user)
=======
    """Список всех уведомлений пользователя"""
    notifications = Notification.objects.filter(user=request.user)
    
    # Фильтр по статусу прочтения
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)
    elif filter_type == 'read':
        notifications = notifications.filter(is_read=True)
<<<<<<< HEAD

    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

=======
    
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
        'filter_type': filter_type,
    }
    return render(request, 'events/notifications.html', context)


@login_required
def notification_mark_read(request, pk):
<<<<<<< HEAD
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

=======
    """Отметить уведомление как прочитанное"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    return redirect('notifications_list')


@login_required
def notification_mark_all_read(request):
<<<<<<< HEAD
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

=======
    """Отметить все уведомления как прочитанные"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    messages.success(request, 'Все уведомления отмечены как прочитанные')
    return redirect('notifications_list')


@login_required
def notifications_unread_count(request):
<<<<<<< HEAD
=======
    """Получить количество непрочитанных уведомлений (AJAX)"""
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def notifications_latest(request):
<<<<<<< HEAD
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:5]
=======
    """Получить последние непрочитанные уведомления (AJAX)"""
    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')[:5]
    
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
    data = {
        'notifications': [
            {
                'id': n.id,
                'type': n.type,
                'title': n.title,
                'message': n.message,
                'icon': n.icon,
                'created_at': n.created_at.strftime('%d.%m.%Y %H:%M'),
<<<<<<< HEAD
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
        messages.error(request, 'У вас нет доступа к этому каналу.')
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
                    title=f'Новое сообщение в канале "{channel.name}"',
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
        messages.error(request, 'Только организатор события может создавать каналы.')
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

            messages.success(request, 'Канал успешно создан.')
            return redirect('chat_channel_detail', channel_id=channel.pk)
    else:
        form = ChatChannelForm()

    return render(request, 'events/chat_channel_form.html', {'event': event, 'form': form})
=======
                'url': f'/events/{n.related_event.pk}/' if n.related_event else None,
            }
            for n in notifications
        ],
        'count': Notification.objects.filter(user=request.user, is_read=False).count()
    }
    return JsonResponse(data)
>>>>>>> 87649b76dfffa07ece7192331d9e7cea6fa6ae8f
