from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .constants import (
    ACTIVE_REGISTRATION_STATUSES,
    APPROVED_REGISTRATION_STATUSES,
    REGISTRATION_ACTIONS,
)
from .forms import EventForm, EventListFilterForm, EventRegistrationForm
from .models import Event, EventRegistration, Skill, apply_event_completion_rewards
from .selectors import events_base_queryset, user_can_access_event_chat
from .services import (
    add_volunteer_to_event_channels,
    notify_registration_approved,
    notify_registration_rejected,
    submit_event_registration,
)


def event_list(request):
    today = date.today()
    tab = request.GET.get('tab', 'current')
    events = events_base_queryset()

    if tab == 'archive':
        events = events.filter(date__lt=today)
    else:
        tab = 'current'
        events = events.filter(date__gte=today)

    filter_form = EventListFilterForm(request.GET or None)

    selected_skill = request.GET.get('skill', '')
    selected_city = request.GET.get('city', '')
    search_query = request.GET.get('search', '')
    selected_type = request.GET.get('event_type', '')
    selected_status = request.GET.get('status', '')
    selected_date_from = request.GET.get('date_from', '')
    selected_date_to = request.GET.get('date_to', '')
    selected_participant = request.GET.get('participant', '')

    if filter_form.is_valid():
        skill = filter_form.cleaned_data['skill']
        city = filter_form.cleaned_data['city']
        search = filter_form.cleaned_data['search']
        event_type = filter_form.cleaned_data['event_type']
        status = filter_form.cleaned_data['status']
        date_from = filter_form.cleaned_data['date_from']
        date_to = filter_form.cleaned_data['date_to']
        participant = filter_form.cleaned_data['participant']

        selected_skill = str(skill.pk) if skill else ''
        selected_city = city
        search_query = search
        selected_type = event_type
        selected_status = status
        selected_date_from = date_from.isoformat() if date_from else ''
        selected_date_to = date_to.isoformat() if date_to else ''
        selected_participant = participant

        if skill:
            events = events.filter(required_skills=skill)
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
    elif request.GET:
        messages.error(request, 'Проверьте корректность параметров фильтрации.')

    events = events.distinct().order_by('date', 'time')
    skills = Skill.objects.all()
    cities = (
        Event.objects.filter(is_active=True)
        .values_list('city', flat=True)
        .exclude(city='')
        .distinct()
    )

    context = {
        'events': events,
        'skills': skills,
        'cities': cities,
        'event_type_choices': Event.TYPE_CHOICES,
        'tab': tab,
        'selected_skill': selected_skill,
        'selected_city': selected_city,
        'search_query': search_query,
        'selected_type': selected_type,
        'selected_status': selected_status,
        'selected_date_from': selected_date_from,
        'selected_date_to': selected_date_to,
        'selected_participant': selected_participant,
    }
    return render(request, 'events/event_list.html', context)


def event_detail(request, pk):
    event = get_object_or_404(
        Event.objects.select_related('organizer__profile').prefetch_related('chat_channels'),
        pk=pk,
    )
    user_registration = None
    can_register = False
    can_open_chat = False
    organizer_registrations_count = None
    event_chat_channel = next(iter(event.chat_channels.all()), None)

    if request.user.is_authenticated:
        user_registration = EventRegistration.objects.filter(event=event, volunteer=request.user).first()
        active_registration_exists = EventRegistration.objects.filter(
            event=event,
            volunteer=request.user,
            status__in=ACTIVE_REGISTRATION_STATUSES,
        ).exists()
        can_register = (
            request.user.profile.is_volunteer
            and not event.is_full
            and not active_registration_exists
            and event.date >= date.today()
        )
        can_open_chat = user_can_access_event_chat(request.user, event)
        if request.user == event.organizer:
            organizer_registrations_count = event.registrations.count()

    context = {
        'event': event,
        'user_registration': user_registration,
        'can_register': can_register,
        'can_open_chat': can_open_chat,
        'event_chat_channel': event_chat_channel,
        'organizer_registrations_count': organizer_registrations_count,
    }
    return render(request, 'events/event_detail.html', context)


@login_required
def event_register(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if not request.user.profile.is_volunteer:
        messages.error(request, 'Только волонтеры могут записываться на события.')
        return redirect('event_detail', pk=pk)

    if event.is_full:
        messages.error(request, 'К сожалению, все места заняты.')
        return redirect('event_detail', pk=pk)

    if event.date < date.today():
        messages.error(request, 'Запись на прошедшее событие недоступна.')
        return redirect('event_detail', pk=pk)

    existing = EventRegistration.objects.filter(event=event, volunteer=request.user).first()
    if existing and existing.status in ACTIVE_REGISTRATION_STATUSES:
        messages.info(request, 'Вы уже записаны на это событие.')
        return redirect('event_detail', pk=pk)

    if request.method == 'POST':
        form = EventRegistrationForm(request.POST)
        if form.is_valid():
            _, success_message = submit_event_registration(
                form=form,
                event=event,
                volunteer=request.user,
                existing_registration=existing,
            )
            messages.success(request, success_message)
            return redirect('event_detail', pk=pk)
    else:
        form = EventRegistrationForm()

    return render(request, 'events/event_register.html', {'event': event, 'form': form})


@login_required
@require_POST
def event_cancel_registration(request, pk):
    event = get_object_or_404(Event, pk=pk)
    registration = get_object_or_404(EventRegistration, event=event, volunteer=request.user)
    if registration.status in ['completed', 'rejected']:
        messages.error(request, 'Эту заявку нельзя отменить.')
        return redirect('event_detail', pk=pk)
    registration.status = 'cancelled'
    registration.save(update_fields=['status', 'updated_at'])
    messages.success(request, 'Запись отменена.')
    return redirect('event_detail', pk=pk)


@login_required
def event_create(request):
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
    event = get_object_or_404(Event, pk=pk)

    if event.organizer != request.user:
        messages.error(request, 'Вы можете управлять только своими событиями.')
        return redirect('event_detail', pk=pk)

    if request.method == 'POST':
        reg_id = request.POST.get('registration_id')
        action = request.POST.get('action')
        if action not in REGISTRATION_ACTIONS:
            messages.error(request, 'Неизвестное действие.')
            return redirect('event_manage', pk=pk)

        with transaction.atomic():
            event_locked = Event.objects.select_for_update().get(pk=event.pk)
            registration = get_object_or_404(
                EventRegistration.objects.select_for_update().select_related('volunteer'),
                pk=reg_id,
                event=event_locked,
            )
            volunteer_name = registration.volunteer.get_full_name() or registration.volunteer.username

            if action == 'approve':
                if registration.status != 'pending':
                    messages.error(request, 'Одобрить можно только заявку со статусом "На рассмотрении".')
                else:
                    approved_count = event_locked.registrations.filter(
                        status__in=APPROVED_REGISTRATION_STATUSES
                    ).count()
                    if approved_count >= event_locked.max_volunteers:
                        messages.error(request, 'Лимит участников уже достигнут.')
                    else:
                        registration.status = 'approved'
                        registration.save(update_fields=['status', 'updated_at'])
                        add_volunteer_to_event_channels(registration.volunteer, event_locked)
                        messages.success(request, f'Заявка {volunteer_name} одобрена.')
                        notify_registration_approved(registration, event_locked)
            elif action == 'reject':
                if registration.status == 'completed':
                    messages.error(request, 'Нельзя отклонить уже завершенного участника.')
                elif registration.status == 'rejected':
                    messages.info(request, 'Заявка уже отклонена.')
                else:
                    registration.status = 'rejected'
                    registration.save(update_fields=['status', 'updated_at'])
                    messages.success(request, f'Заявка {volunteer_name} отклонена.')
                    notify_registration_rejected(registration, event_locked)
            elif event_locked.date > date.today():
                messages.error(request, 'Нельзя завершить участие до даты события.')
            elif registration.status == 'completed':
                messages.info(request, 'Участие уже завершено.')
            elif registration.status != 'approved':
                messages.error(request, 'Завершить можно только одобренного участника.')
            else:
                registration.status = 'completed'
                registration.completed_at = timezone.now()
                registration.save(update_fields=['status', 'completed_at', 'updated_at'])
                apply_event_completion_rewards(registration)
                messages.success(
                    request,
                    f'Участие {volunteer_name} завершено, XP и достижения обновлены.',
                )

    registrations = event.registrations.select_related('volunteer__profile').prefetch_related(
        'volunteer__profile__skills'
    )
    return render(request, 'events/event_manage.html', {'event': event, 'registrations': registrations})


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
