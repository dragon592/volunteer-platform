from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import UserProfileForm, VolunteerSearchForm
from .models import Event, EventRegistration, UserProfile, VolunteerAchievement
from .controllers.profile_controller import ProfileController


@login_required
def profile_view(request):
    """Профиль пользователя"""
    try:
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'Профиль не найден.')
            return redirect('event_list')
        
        if request.method == 'POST':
            form = UserProfileForm(
                request.POST,
                request.FILES,
                instance=request.user.profile,
                user=request.user
            )
            if form.is_valid():
                ProfileController.update_profile(request, form)
                messages.success(request, 'Профиль обновлен!')
                return redirect('profile')
        else:
            form = UserProfileForm(instance=request.user.profile, user=request.user)
        
        # Получаем данные через контроллер
        profile_data = ProfileController.get_user_profile(request)
        
        context = {
            'form': form,
            'my_events': profile_data['my_events'],
            'achievements': profile_data['achievements'],
            'xp_progress_percent': profile_data['xp_progress_percent'],
            'upcoming_events': profile_data['upcoming_events'],
            'past_events': profile_data['past_events'],
            'completed_events_count': profile_data['completed_events_count'],
            'total_participants': profile_data['total_participants'],
        }
        return render(request, 'events/profile.html', context)
    except Exception as e:
        messages.error(request, f'Ошибка загрузки профиля: {str(e)}')
        return redirect('event_list')


@login_required
def volunteer_search(request):
    """Поиск волонтеров"""
    try:
        context = ProfileController.get_volunteer_search_results(request)
        return render(request, 'events/volunteer_search.html', context)
    except Exception as e:
        messages.error(request, f'Ошибка поиска: {str(e)}')
        return redirect('event_list')


@login_required
def volunteer_profile(request, pk):
    """Профиль волонтера"""
    try:
        context = ProfileController.get_volunteer_profile(request, pk)
        return render(request, 'events/volunteer_profile.html', context)
    except Exception as e:
        messages.error(request, f'Ошибка загрузки профиля волонтера: {str(e)}')
        return redirect('event_list')


@login_required
def leaderboard_view(request):
    """Таблица лидеров"""
    try:
        leaderboard_data = ProfileController.get_leaderboard()
        context = {
            'leaderboard_data': leaderboard_data,
        }
        return render(request, 'events/leaderboard.html', context)
    except Exception as e:
        messages.error(request, f'Ошибка загрузки таблицы лидеров: {str(e)}')
        return redirect('event_list')
