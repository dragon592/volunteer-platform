from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .decorators import rate_limit
from .models import Notification
from .controllers.notification_controller import NotificationController


@login_required
def notifications_list(request):
    """Список уведомлений"""
    try:
        context = NotificationController.get_notifications_list(request)
        return render(request, 'events/notifications.html', context)
    except Exception as e:
        messages.error(request, f'Ошибка загрузки уведомлений: {str(e)}')
        return redirect('event_list')


@login_required
@require_POST
def notification_mark_read(request, pk):
    """Отметить уведомление как прочитанное"""
    try:
        result = NotificationController.mark_notification_read(request, pk)
        if result:
            return result
        return redirect('notifications_list')
    except Exception as e:
        messages.error(request, f'Ошибка: {str(e)}')
        return redirect('notifications_list')


@login_required
@require_POST
def notification_mark_all_read(request):
    """Отметить все уведомления как прочитанные"""
    try:
        result = NotificationController.mark_all_notifications_read(request)
        if result:
            return result
        return redirect('notifications_list')
    except Exception as e:
        messages.error(request, f'Ошибка: {str(e)}')
        return redirect('notifications_list')


@login_required
@rate_limit('notifications_count', limit=180, window_seconds=60)
def notifications_unread_count(request):
    """API: количество непрочитанных уведомлений"""
    return NotificationController.get_unread_count(request)


@login_required
@rate_limit('notifications_latest', limit=120, window_seconds=60)
def notifications_latest(request):
    """API: последние непрочитанные уведомления"""
    return NotificationController.get_latest_notifications(request)
