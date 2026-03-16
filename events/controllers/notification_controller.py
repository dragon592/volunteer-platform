"""
Контроллер для управления уведомлениями.
"""
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q

from events.models import Notification
from events.decorators import rate_limit


class NotificationController:
    """Контроллер для операций с уведомлениями"""
    
    @staticmethod
    def get_notifications_list(request):
        """Получает список уведомлений пользователя с фильтрацией"""
        if not hasattr(request.user, 'profile'):
            raise ValueError('Профиль не найден.')
        
        notifications_qs = Notification.objects.filter(
            user=request.user
        ).select_related('related_event')
        
        filter_type = request.GET.get('filter', 'all')
        if filter_type == 'unread':
            notifications_qs = notifications_qs.filter(is_read=False)
        elif filter_type == 'read':
            notifications_qs = notifications_qs.filter(is_read=True)
        
        from django.core.paginator import Paginator
        paginator = Paginator(notifications_qs, 20)
        page_obj = paginator.get_page(request.GET.get('page', 1))
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        
        return {
            'notifications': page_obj.object_list,
            'page_obj': page_obj,
            'unread_count': unread_count,
            'filter_type': filter_type,
        }
    
    @staticmethod
    def mark_notification_read(request, pk):
        """Отмечает уведомление как прочитанное"""
        if not hasattr(request.user, 'profile'):
            raise ValueError('Профиль не найден.')
        
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        return None  # Перенаправление обрабатывается в view
    
    @staticmethod
    def mark_all_notifications_read(request):
        """Отмечает все уведомления как прочитанные"""
        if not hasattr(request.user, 'profile'):
            raise ValueError('Профиль не найден.')
        
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        messages.success(request, 'Все уведомления отмечены как прочитанные')
        return None
    
    @staticmethod
    @rate_limit('notifications_count', limit=180, window_seconds=60)
    def get_unread_count(request):
        """Возвращает количество непрочитанных уведомлений (API)"""
        if not hasattr(request.user, 'profile'):
            return JsonResponse({'count': 0}, status=200)
        
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return JsonResponse({'count': count})
    
    @staticmethod
    @rate_limit('notifications_latest', limit=120, window_seconds=60)
    def get_latest_notifications(request):
        """Возвращает последние непрочитанные уведомления (API)"""
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
                    'url': n.get_absolute_url() if n.related_event else None,
                }
                for n in notifications
            ],
            'count': count,
        }
        return JsonResponse(data)
