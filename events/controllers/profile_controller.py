"""
Контроллер для управления профилями пользователей.
"""
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.utils import timezone

from events.models import UserProfile, Event, EventRegistration, VolunteerAchievement
from events.forms import UserProfileForm, VolunteerSearchForm


class ProfileController:
    """Контроллер для операций с профилями"""
    
    @staticmethod
    def get_user_profile(request):
        """Получает профиль текущего пользователя"""
        user = request.user
        
        if not hasattr(user, 'profile'):
            raise ValueError('Профиль не найден.')
        
        profile = user.profile
        
        # Статистика в зависимости от роли
        if profile.is_organizer:
            my_events = Event.objects.filter(organizer=user, is_active=True)
            upcoming_events = my_events.filter(date__gte=timezone.localdate()).count()
            past_events = my_events.filter(date__lt=timezone.localdate()).count()
            total_participants = EventRegistration.objects.filter(
                event__organizer=user,
                status__in=['approved', 'completed']
            ).count()
            achievements = None
            completed_events_count = 0
        else:
            my_events = (
                Event.objects.filter(
                    registrations__volunteer=user,
                    registrations__status__in=['pending', 'approved', 'completed'],
                    is_active=True,
                )
                .select_related('organizer')
                .prefetch_related('required_skills')
                .distinct()
            )
            upcoming_events = my_events.filter(date__gte=timezone.localdate()).count()
            past_events = my_events.filter(date__lt=timezone.localdate()).count()
            completed_events_count = EventRegistration.objects.filter(
                volunteer=user,
                status='completed'
            ).count()
            achievements = (
                VolunteerAchievement.objects.filter(volunteer=user)
                .select_related('achievement')
                .order_by('-awarded_at')
            )
            total_participants = None
        
        return {
            'profile': profile,
            'my_events': my_events,
            'achievements': achievements,
            'xp_progress_percent': profile.xp % 100,
            'upcoming_events': upcoming_events,
            'past_events': past_events,
            'completed_events_count': completed_events_count,
            'total_participants': total_participants,
        }
    
    @staticmethod
    def update_profile(request, form):
        """Обновляет профиль пользователя"""
        if not form.is_valid():
            raise ValueError('Форма невалидна')
        
        form.save()
        return form.instance
    
    @staticmethod
    def get_volunteer_search_results(request):
        """Поиск волонтеров (только для организаторов)"""
        user = request.user
        
        if not hasattr(user, 'profile') or not user.profile.is_organizer:
            raise ValueError('Только организаторы могут искать волонтеров.')
        
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
        
        return {
            'volunteers': volunteers,
            'form': form,
        }
    
    @staticmethod
    def get_volunteer_profile(request, pk):
        """Получает профиль конкретного волонтера"""
        user = request.user
        
        if not hasattr(user, 'profile') or not user.profile.is_organizer:
            raise ValueError('Доступ к профилям волонтеров доступен только организаторам.')
        
        profile = get_object_or_404(
            UserProfile.objects.select_related('user').prefetch_related('skills'),
            pk=pk,
            role='volunteer',
        )
        
        completed_events = EventRegistration.objects.filter(
            volunteer=profile.user,
            status='completed',
        ).count()
        achievements = VolunteerAchievement.objects.filter(
            volunteer=profile.user
        ).select_related('achievement')
        
        return {
            'volunteer_profile': profile,
            'completed_events': completed_events,
            'achievements': achievements,
        }
    
    @staticmethod
    def get_leaderboard():
        """Получает данные для таблицы лидеров"""
        from django.db.models import Count, Q
        
        volunteers = UserProfile.objects.filter(role='volunteer').select_related('user')
        
        # Аннотируем количество завершенных событий
        volunteers = volunteers.annotate(
            completed_events_count=Count(
                'user__event_registrations',
                filter=Q(user__event_registrations__status='completed')
            )
        )
        
        # Сортируем по XP и завершенным событиям
        volunteers = volunteers.order_by('-xp', '-completed_events_count', 'user__date_joined')
        
        # Prefetch skills
        volunteers = volunteers.prefetch_related('skills')
        
        # Добавляем ранги
        leaderboard_data = []
        for idx, profile in enumerate(volunteers, start=1):
            leaderboard_data.append({
                'rank': idx,
                'profile': profile,
                'xp': profile.xp,
                'level_name': profile.level_name,
                'level_icon': profile.level_icon,
                'completed_events': profile.completed_events_count,
            })
        
        return leaderboard_data
