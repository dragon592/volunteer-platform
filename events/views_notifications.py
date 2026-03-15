from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .decorators import rate_limit
from .models import Notification


@login_required
def notifications_list(request):
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Профиль не найден.')
        return redirect('event_list')
    notifications_qs = Notification.objects.filter(user=request.user).select_related('related_event')
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'unread':
        notifications_qs = notifications_qs.filter(is_read=False)
    elif filter_type == 'read':
        notifications_qs = notifications_qs.filter(is_read=True)

    paginator = Paginator(notifications_qs, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    context = {
        'notifications': page_obj.object_list,
        'page_obj': page_obj,
        'unread_count': unread_count,
        'filter_type': filter_type,
    }
    return render(request, 'events/notifications.html', context)


@login_required
@require_POST
def notification_mark_read(request, pk):
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Профиль не найден.')
        return redirect('event_list')
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    return redirect('notifications_list')


@login_required
@require_POST
def notification_mark_all_read(request):
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Профиль не найден.')
        return redirect('event_list')
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    messages.success(request, 'Все уведомления отмечены как прочитанные')
    return redirect('notifications_list')


@login_required
@rate_limit('notifications_count', limit=180, window_seconds=60)
def notifications_unread_count(request):
    if not hasattr(request.user, 'profile'):
        return JsonResponse({'count': 0}, status=200)
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@login_required
@rate_limit('notifications_latest', limit=120, window_seconds=60)
def notifications_latest(request):
    if not hasattr(request.user, 'profile'):
        return JsonResponse({'notifications': [], 'count': 0}, status=200)
    unread_qs = (
        Notification.objects.filter(user=request.user, is_read=False)
        .select_related('related_event')
        .order_by('-created_at')
    )
    count = unread_qs.count()
    notifications = list(unread_qs[:5])
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
        'count': count,
    }
    return JsonResponse(data)
