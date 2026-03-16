from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
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
from .controllers.event_controller import EventController
from .controllers.chat_controller import ChatController


def event_list(request):
    """Список событий с фильтрацией"""
    try:
        context = EventController.get_event_list(request)
        return render(request, 'events/event_list.html', context)
    except Exception as e:
        messages.error(request, f'Ошибка загрузки событий: {str(e)}')
        return redirect('event_list')


def event_detail(request, pk):
    """Детальная информация о событии"""
    try:
        context = EventController.get_event_detail(request, pk)
        return render(request, 'events/event_detail.html', context)
    except Exception as e:
        messages.error(request, f'Ошибка загрузки события: {str(e)}')
        return redirect('event_list')


@login_required
def event_create(request):
    """Создание нового события"""
    try:
        if request.method == 'POST':
            form = EventForm(request.POST, request.FILES)
            if form.is_valid():
                event = EventController.create_event(request, form)
                messages.success(request, 'Событие успешно создано!')
                return redirect('event_detail', pk=event.pk)
        else:
            form = EventForm()
        
        context = {
            'form': form,
            'event_types': Event.TYPE_CHOICES,
            'skills': Skill.objects.all(),
        }
        return render(request, 'events/event_form.html', context)
    except Exception as e:
        messages.error(request, f'Ошибка создания события: {str(e)}')
        return redirect('event_list')


@login_required
def event_edit(request, pk):
    """Редактирование события"""
    try:
        event = get_object_or_404(Event, pk=pk, organizer=request.user)
        
        if request.method == 'POST':
            form = EventForm(request.POST, request.FILES, instance=event)
            if form.is_valid():
                event = EventController.update_event(request, pk, form)
                messages.success(request, 'Событие успешно обновлено!')
                return redirect('event_detail', pk=event.pk)
        else:
            form = EventForm(instance=event)
        
        context = {
            'form': form,
            'event': event,
            'event_types': Event.TYPE_CHOICES,
            'skills': Skill.objects.all(),
        }
        return render(request, 'events/event_form.html', context)
    except Exception as e:
        messages.error(request, f'Ошибка редактирования события: {str(e)}')
        return redirect('event_list')


@login_required
def event_delete(request, pk):
    """Удаление события (soft delete)"""
    try:
        event = EventController.delete_event(request, pk)
        messages.success(request, 'Событие удалено.')
        return redirect('event_list')
    except Exception as e:
        messages.error(request, f'Ошибка удаления события: {str(e)}')
        return redirect('event_detail', pk=pk)


@login_required
def event_register(request, pk):
    """Регистрация на событие"""
    try:
        if request.method == 'POST':
            form = EventRegistrationForm(request.POST)
            if form.is_valid():
                registration, success_message = EventController.register_for_event(
                    request, pk, form
                )
                messages.success(request, success_message)
                return redirect('event_detail', pk=pk)
        else:
            form = EventRegistrationForm()
        
        event = get_object_or_404(Event, pk=pk)
        context = {
            'event': event,
            'form': form,
        }
        return render(request, 'events/event_register.html', context)
    except Exception as e:
        messages.error(request, f'Ошибка регистрации: {str(e)}')
        return redirect('event_detail', pk=pk)


@login_required
def event_cancel_registration(request, pk):
    """Отмена регистрации на событие"""
    try:
        registration = EventController.cancel_registration(request, pk)
        messages.success(request, 'Регистрация отменена.')
        return redirect('event_detail', pk=pk)
    except Exception as e:
        messages.error(request, f'Ошибка отмены регистрации: {str(e)}')
        return redirect('event_detail', pk=pk)


@login_required
def event_manage_registrations(request, pk):
    """Управление регистрациями (для организаторов)"""
    try:
        event = get_object_or_404(Event, pk=pk, organizer=request.user)
        registrations = event.registrations.select_related('volunteer__profile').order_by('-created_at')
        
        if request.method == 'POST':
            registration_id = request.POST.get('registration_id')
            new_status = request.POST.get('status')
            
            if registration_id and new_status:
                registration = get_object_or_404(EventRegistration, id=registration_id, event=event)
                old_status = registration.status
                registration.status = new_status
                registration.save()
                
                # Логика начисления XP при завершении
                if new_status == 'completed' and not registration.xp_awarded:
                    apply_event_completion_rewards(registration)
                    registration.xp_awarded = True
                    registration.save(update_fields=['xp_awarded'])
                
                messages.success(request, f'Статус заявки обновлен на "{registration.get_status_display()}".')
            
            return redirect('event_manage', pk=pk)
        
        context = {
            'event': event,
            'registrations': registrations,
        }
        return render(request, 'events/event_manage.html', context)
    except Exception as e:
        messages.error(request, f'Ошибка управления регистрациями: {str(e)}')
        return redirect('event_detail', pk=pk)


@login_required
def my_events(request):
    """Мои события (как организатор и как участник)"""
    try:
        context = EventController.get_user_events(request)
        return render(request, 'events/my_events.html', context)
    except Exception as e:
        messages.error(request, f'Ошибка загрузки событий: {str(e)}')
        return redirect('event_list')
