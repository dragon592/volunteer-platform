"""
Контроллер для управления событиями.
Отделяет бизнес-логику от view-функций.
"""
from django.db import transaction
from django.db.models import Count, F, Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib import messages

from events.models import Event, EventRegistration, Skill
from events.forms import EventListFilterForm
from events.selectors import events_base_queryset, user_can_access_event_chat
from events.services import (
    submit_event_registration,
    notify_event_created,
    notify_event_updated,
    add_volunteer_to_event_channels,
    remove_volunteer_from_event_channels,
)


class EventController:
    """Контроллер для операций с событиями"""
    
    @staticmethod
    def get_event_list(request):
        """
        Получает список событий с фильтрацией и пагинацией.
        Возвращает context для шаблона.
        """
        today = timezone.localdate()
        tab = request.GET.get('tab', 'current')
        events = events_base_queryset()
        
        if tab == 'archive':
            events = events.filter(date__lt=today)
        else:
            tab = 'current'
            events = events.filter(date__gte=today)
        
        # Применяем фильтры
        filter_form = EventListFilterForm(request.GET or None)
        
        selected_skill = request.GET.get('skill', '')
        selected_city = request.GET.get('city', '')
        search_query = request.GET.get('search', '')
        selected_type = request.GET.get('event_type', '')
        selected_status = request.GET.get('status', '')
        selected_date_from = request.GET.get('date_from', '')
        selected_date_to = request.GET.get('date_to', '')
        selected_participant = request.GET.get('participant', '')
        selected_sort = request.GET.get('sort', 'date_asc')
        sort_by = selected_sort
        
        if filter_form.is_valid():
            skill = filter_form.cleaned_data['skill']
            city = filter_form.cleaned_data['city']
            search = filter_form.cleaned_data['search']
            event_type = filter_form.cleaned_data['event_type']
            status = filter_form.cleaned_data['status']
            date_from = filter_form.cleaned_data['date_from']
            date_to = filter_form.cleaned_data['date_to']
            participant = filter_form.cleaned_data['participant']
            sort_by = filter_form.cleaned_data.get('sort', 'date_asc')
            
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
            events = events.distinct()
        elif request.GET:
            messages.error(request, 'Проверьте корректность параметров фильтрации.')
        
        # Сортировка
        sort_options = {
            'date_asc': ['date', 'time'],
            'date_desc': ['-date', '-time'],
            'popular': ['-approved_participants', 'date'],
            'participants': ['-approved_participants', 'date'],
        }
        if sort_by in sort_options:
            events = events.order_by(*sort_options[sort_by])
        else:
            events = events.order_by('date', 'time')
        
        # Пагинация
        paginator = Paginator(events, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Получаем справочные данные
        skills = Skill.objects.all()
        cities = (
            Event.objects.filter(is_active=True)
            .values_list('city', flat=True)
            .exclude(city='')
            .distinct()
        )
        
        return {
            'events': page_obj,
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
            'selected_sort': selected_sort,
        }
    
    @staticmethod
    def get_event_detail(request, pk):
        """Получает детальную информацию о событии"""
        event = get_object_or_404(
            events_base_queryset().prefetch_related(
                'chat_channels',
                'registrations__volunteer__profile'
            ),
            pk=pk,
        )
        
        user_registration = None
        can_register = False
        can_open_chat = False
        organizer_registrations_count = None
        
        # Получаем список одобренных участников
        approved_participants = event.registrations.filter(
            status__in=['approved', 'completed']
        ).select_related('volunteer__profile').order_by('created_at')
        
        if request.user.is_authenticated:
            user_registration = EventRegistration.objects.filter(
                event=event,
                volunteer=request.user
            ).first()
            
            active_registration_exists = EventRegistration.objects.filter(
                event=event,
                volunteer=request.user,
                status__in=['pending', 'approved', 'completed'],
            ).exists()
            
            can_register = (
                hasattr(request.user, 'profile') and request.user.profile.is_volunteer
                and not event.is_full
                and not active_registration_exists
                and event.date >= timezone.localdate()
            )
            
            can_open_chat = user_can_access_event_chat(request.user, event)
            
            if request.user == event.organizer:
                organizer_registrations_count = event.registrations.count()
        
        return {
            'event': event,
            'user_registration': user_registration,
            'can_register': can_register,
            'can_open_chat': can_open_chat,
            'event_chat_channel': event.chat_channels.filter(is_archived=False).first(),
            'organizer_registrations_count': organizer_registrations_count,
            'approved_participants': approved_participants,
        }
    
    @staticmethod
    @transaction.atomic
    def create_event(request, form):
        """Создает новое событие"""
        if not form.is_valid():
            raise ValueError('Форма невалидна')
        
        event = form.save(commit=False)
        event.organizer = request.user
        event.save()
        form.save_m2m()
        
        # Отправляем уведомления волонтерам
        notify_event_created(event, exclude_user=request.user)
        
        return event
    
    @staticmethod
    @transaction.atomic
    def update_event(request, pk, form):
        """Обновляет существующее событие"""
        event = get_object_or_404(Event, pk=pk, organizer=request.user)
        
        if not form.is_valid():
            raise ValueError('Форма невалидна')
        
        event = form.save()
        notify_event_updated(event)
        return event
    
    @staticmethod
    @transaction.atomic
    def delete_event(request, pk):
        """Удаляет событие"""
        event = get_object_or_404(Event, pk=pk, organizer=request.user)
        event.is_active = False
        event.save()
        return event
    
    @staticmethod
    @transaction.atomic
    def register_for_event(request, pk, form):
        """Регистрирует пользователя на событие"""
        event = get_object_or_404(Event.objects.filter(is_active=True), pk=pk)
        
        # Проверяем наличие профиля и роль
        if not hasattr(request.user, 'profile') or not request.user.profile.is_volunteer:
            raise ValueError('Только волонтеры могут записываться на события.')
        
        registration, success_message = submit_event_registration(
            form=form,
            event=event,
            volunteer=request.user
        )
        
        # Добавляем пользователя в каналы чата события
        if registration.status in ['pending', 'approved']:
            add_volunteer_to_event_channels(request.user, event)
        
        return registration, success_message
    
    @staticmethod
    @transaction.atomic
    def cancel_registration(request, pk):
        """Отменяет регистрацию на событие"""
        event = get_object_or_404(Event, pk=pk, is_active=True)
        
        registration = get_object_or_404(
            EventRegistration,
            event=event,
            volunteer=request.user,
            status__in=['pending', 'approved']
        )
        
        old_status = registration.status
        registration.status = 'cancelled'
        registration.save()
        
        # Удаляем из каналов чата
        remove_volunteer_from_event_channels(request.user, event)
        
        return registration
    
    @staticmethod
    def get_user_events(request):
        """Получает события пользователя (как организатор и как участник)"""
        user = request.user
        
        # События, которые пользователь организует
        organized_events = Event.objects.filter(
            organizer=user,
            is_active=True
        ).select_related('organizer').prefetch_related('required_skills')
        
        # События, на которые пользователь записан
        registered_events = (
            Event.objects.filter(
                registrations__volunteer=user,
                registrations__status__in=['pending', 'approved', 'completed'],
                is_active=True,
            )
            .select_related('organizer')
            .prefetch_related('required_skills')
            .distinct()
        )
        
        return {
            'organized_events': organized_events,
            'registered_events': registered_events,
        }
