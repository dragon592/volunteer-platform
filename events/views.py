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
    
    if skill_id:
        events = events.filter(required_skills__id=skill_id)
    if city:
        events = events.filter(city__icontains=city)
    if search:
        events = events.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )
    
    events = events.distinct().order_by('date')
    skills = Skill.objects.all()
    cities = Event.objects.values_list('city', flat=True).distinct().exclude(city='')
    
    context = {
        'events': events,
        'skills': skills,
        'cities': cities,
        'selected_skill': skill_id,
        'selected_city': city,
        'search_query': search,
    }
    return render(request, 'events/event_list.html', context)


def event_detail(request, pk):
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
    
    context = {
        'event': event,
        'user_registration': user_registration,
        'can_register': can_register,
        'registrations': registrations,
    }
    return render(request, 'events/event_detail.html', context)


@login_required
def event_register(request, pk):
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
    
    if request.method == 'POST':
        form = EventRegistrationForm(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.event = event
            registration.volunteer = request.user
            registration.save()
            messages.success(request, 'Вы успешно записались на событие!')
            # Создаём уведомление для организатора
            Notification.objects.create(
                user=event.organizer,
                type='new_application',
                title='Новая заявка на событие',
                message=f'{request.user.get_full_name()} подал заявку на событие "{event.title}".',
                related_event=event,
                related_registration=registration
            )
            return redirect('event_detail', pk=pk)
    else:
        form = EventRegistrationForm()
    
    return render(request, 'events/event_register.html', {'event': event, 'form': form})


@login_required
def event_cancel_registration(request, pk):
    """Отмена записи на событие"""
    event = get_object_or_404(Event, pk=pk)
    registration = get_object_or_404(
        EventRegistration, event=event, volunteer=request.user
    )
    registration.status = 'cancelled'
    registration.save()
    messages.success(request, 'Запись отменена.')
    return redirect('event_detail', pk=pk)


@login_required
def event_create(request):
    """Создание события (только для организаторов)"""
    if not request.user.profile.is_organizer:
        messages.error(request, 'Только организаторы могут создавать события.')
        return redirect('event_list')
    
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
    
    return render(request, 'events/event_form.html', {'form': form, 'title': 'Создать событие'})


@login_required
def event_edit(request, pk):
    """Редактирование события"""
    event = get_object_or_404(Event, pk=pk)
    
    if event.organizer != request.user:
        messages.error(request, 'Вы можете редактировать только свои события.')
        return redirect('event_detail', pk=pk)
    
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Событие обновлено!')
            return redirect('event_detail', pk=pk)
    else:
        form = EventForm(instance=event)
    
    return render(request, 'events/event_form.html', {'form': form, 'title': 'Редактировать событие', 'event': event})


@login_required
def event_manage_registrations(request, pk):
    """Управление заявками на событие (для организатора)"""
    event = get_object_or_404(Event, pk=pk)
    
    if event.organizer != request.user:
        messages.error(request, 'Вы можете управлять только своими событиями.')
        return redirect('event_detail', pk=pk)
    
    if request.method == 'POST':
        reg_id = request.POST.get('registration_id')
        action = request.POST.get('action')
        registration = get_object_or_404(EventRegistration, pk=reg_id, event=event)
        
        if action == 'approve':
            registration.status = 'approved'
            messages.success(request, f'Заявка {registration.volunteer.get_full_name()} одобрена.')
            # Создаём уведомление для волонтёра
            Notification.objects.create(
                user=registration.volunteer,
                type='application_approved',
                title='Заявка одобрена!',
                message=f'Ваша заявка на событие "{event.title}" была одобрена.',
                related_event=event,
                related_registration=registration
            )
        elif action == 'reject':
            registration.status = 'rejected'
            messages.success(request, f'Заявка {registration.volunteer.get_full_name()} отклонена.')
            # Создаём уведомление для волонтёра
            Notification.objects.create(
                user=registration.volunteer,
                type='application_rejected',
                title='Заявка отклонена',
                message=f'К сожалению, ваша заявка на событие "{event.title}" была отклонена.',
                related_event=event,
                related_registration=registration
            )
        registration.save()
    
    registrations = event.registrations.select_related('volunteer__profile')
    return render(request, 'events/event_manage.html', {'event': event, 'registrations': registrations})


def register_view(request):
    """Регистрация нового пользователя"""
    if request.user.is_authenticated:
        return redirect('event_list')
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Добро пожаловать! Ваш аккаунт создан.')
            return redirect('profile')
    else:
        form = UserRegisterForm()
    
    return render(request, 'events/register.html', {'form': form})


def login_view(request):
    """Авторизация"""
    if request.user.is_authenticated:
        return redirect('event_list')
    
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
    
    return render(request, 'events/login.html', {'form': form})


def logout_view(request):
    """Выход"""
    logout(request)
    messages.success(request, 'Вы вышли из системы.')
    return redirect('event_list')


@login_required
def profile_view(request):
    """Просмотр и редактирование профиля"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile, user=request.user)
        if form.is_valid():
            form.save()
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
    }
    return render(request, 'events/profile.html', context)


@login_required
def my_events(request):
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
    }
    return render(request, 'events/my_events.html', context)


@login_required
def volunteer_search(request):
    """Поиск волонтёров (только для организаторов)"""
    if not request.user.profile.is_organizer:
        messages.error(request, 'Только организаторы могут искать волонтёров.')
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
    }
    return render(request, 'events/volunteer_profile.html', context)


@login_required
def notifications_list(request):
    """Список всех уведомлений пользователя"""
    notifications = Notification.objects.filter(user=request.user)
    
    # Фильтр по статусу прочтения
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
    """Отметить уведомление как прочитанное"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notifications_list')


@login_required
def notification_mark_all_read(request):
    """Отметить все уведомления как прочитанные"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'Все уведомления отмечены как прочитанные')
    return redirect('notifications_list')


@login_required
def notifications_unread_count(request):
    """Получить количество непрочитанных уведомлений (AJAX)"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def notifications_latest(request):
    """Получить последние непрочитанные уведомления (AJAX)"""
    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')[:5]
    
    data = {
        'notifications': [
            {
                'id': n.id,
                'type': n.type,
                'title': n.title,
                'message': n.message,
                'icon': n.icon,
                'created_at': n.created_at.strftime('%d.%m.%Y %H:%M'),
                'url': f'/events/{n.related_event.pk}/' if n.related_event else None,
            }
            for n in notifications
        ],
        'count': Notification.objects.filter(user=request.user, is_read=False).count()
    }
    return JsonResponse(data)
