from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import UserProfileForm, VolunteerSearchForm
from .models import Event, EventRegistration, UserProfile, VolunteerAchievement


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлен!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user.profile, user=request.user)

    if request.user.profile.is_organizer:
        my_events = Event.objects.filter(organizer=request.user)
        achievements = None
    else:
        my_events = (
            Event.objects.filter(
                registrations__volunteer=request.user,
                registrations__status__in=['pending', 'approved', 'completed'],
            )
            .select_related('organizer')
            .prefetch_related('required_skills')
            .distinct()
        )
        achievements = (
            VolunteerAchievement.objects.filter(volunteer=request.user)
            .select_related('achievement')
            .order_by('-awarded_at')
        )

    context = {
        'form': form,
        'my_events': my_events,
        'achievements': achievements,
        'xp_progress_percent': request.user.profile.xp % 100,
    }
    return render(request, 'events/profile.html', context)


@login_required
def volunteer_search(request):
    if not request.user.profile.is_organizer:
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
    if not request.user.profile.is_organizer:
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
