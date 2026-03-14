from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from ...models import Event, EventRegistration, Notification


class Command(BaseCommand):
    help = 'Send reminders to volunteers about upcoming events (24 hours before)'

    def handle(self, *args, **options):
        now = timezone.localdate()
        tomorrow = now + timedelta(days=1)
        
        # Находим события, которые состоятся завтра
        upcoming_events = Event.objects.filter(
            date=tomorrow,
            is_active=True
        ).prefetch_related('registrations')
        
        reminders_sent = 0
        
        for event in upcoming_events:
            # Получаем одобренных участников
            approved_registrations = event.registrations.filter(
                status__in=['approved', 'completed']
            ).select_related('volunteer')
            
            for registration in approved_registrations:
                # Проверяем, не было ли уже напоминания
                existing_reminder = Notification.objects.filter(
                    user=registration.volunteer,
                    type='event_reminder',
                    related_event=event,
                    created_at__date=now
                ).exists()
                
                if not existing_reminder:
                    Notification.objects.create(
                        user=registration.volunteer,
                        type='event_reminder',
                        title='Напоминание о событии',
                        message=f'Напоминаем, что завтра вы участвуете в событии "{event.title}". Место: {event.location}.',
                        related_event=event,
                        related_registration=registration,
                    )
                    reminders_sent += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Отправлено {reminders_sent} напоминаний о {upcoming_events.count()} событиях')
        )