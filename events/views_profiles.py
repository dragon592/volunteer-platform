from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import UserProfileForm, VolunteerSearchForm
from .models import Event, EventRegistration, UserProfile, VolunteerAchievement


@login_required
def profile_view(request):
    # Проверяем наличие профиля
    if not hasattr(request.user, 'profile'):
        messages.error(request, 'Профиль не найден.')
        return redirect('event_list')
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлен!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user.profile, user=request.user)

    if request.user.profile.is_organizer:
        my_events = Event.objects.filter(organizer=request.user, is_active=True)
        upcoming_events = my_events.filter(date__gte=timezone.localdate()).count()
        past_events = my_events.filter(date__lt=timezone.localdate()).count()
        total_participants = EventRegistration.objects.filter(
            event__organizer=request.user,
            status__in=['approved', 'completed']
        ).count()
        achievements = None
        completed_events_count = 0
    else:
        my_events = (
            Event.objects.filter(
                registrations__volunteer=request.user,
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
            volunteer=request.user,
            status='completed'
        ).count()
        achievements = (
            VolunteerAchievement.objects.filter(volunteer=request.user)
            .select_related('achievement')
            .order_by('-awarded_at')
        )
        total_participants = None

    context = {
        'form': form,
        'my_events': my_events,
        'achievements': achievements,
        'xp_progress_percent': request.user.profile.xp % 100,
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'completed_events_count': completed_events_count,
        'total_participants': total_participants,
    }
    return render(request, 'events/profile.html', context)


@login_required
def volunteer_search(request):
    if not hasattr(request.user, 'profile') or not request.user.profile.is_organizer:
        messages.error(request, 'Только организаторы могут искать волонтеров.')
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


@login_required
def volunteer_profile(request, pk):
    if not hasattr(request.user, 'profile') or not request.user.profile.is_organizer:
        messages.error(request, 'Доступ к профилям волонтеров доступен только организаторам.')
        return redirect('event_list')

    profile = get_object_or_404(
        UserProfile.objects.select_related('user').prefetch_related('skills'),
        pk=pk,
        role='volunteer',
    )

    completed_events = EventRegistration.objects.filter(
        volunteer=profile.user,
        status='completed',
    ).count()
    achievements = VolunteerAchievement.objects.filter(volunteer=profile.user).select_related('achievement')

    context = {
        'volunteer_profile': profile,
        'completed_events': completed_events,
        'achievements': achievements,
    }
    return render(request, 'events/volunteer_profile.html', context)
