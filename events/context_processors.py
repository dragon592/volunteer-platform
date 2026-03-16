from django.conf import settings
from events.models import Event, Skill, UserProfile


def filter_options(request):
    """
    Provides filter options for the header search form.
    Available on all pages.
    """
    # Get unique cities from events
    cities = Event.objects.filter(is_active=True).exclude(city='').values_list('city', flat=True).distinct().order_by('city')
    
    # Get all skills
    skills = Skill.objects.all().order_by('name')
    
    # Get event type choices from model
    event_type_choices = Event.TYPE_CHOICES
    
    # Get current filter values from request
    selected_type = request.GET.get('event_type', '')
    selected_city = request.GET.get('city', '')
    selected_skill = request.GET.get('skill', '')
    selected_date_from = request.GET.get('date_from', '')
    selected_date_to = request.GET.get('date_to', '')
    selected_status = request.GET.get('status', '')
    
    return {
        'cities': list(cities),
        'skills': skills,
        'event_type_choices': event_type_choices,
        'selected_type': selected_type,
        'selected_city': selected_city,
        'selected_skill': selected_skill,
        'selected_date_from': selected_date_from,
        'selected_date_to': selected_date_to,
        'selected_status': selected_status,
    }
