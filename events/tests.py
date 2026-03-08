from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import ChatChannelMembership, Event, EventRegistration, Notification


class BaseEventsTestCase(TestCase):
    password = 'StrongPassword123!'

    def create_user(self, username, role='volunteer'):
        user = User.objects.create_user(
            username=username,
            email=f'{username}@example.com',
            password=self.password,
            first_name=username.capitalize(),
            last_name='User',
        )
        user.profile.role = role
        user.profile.save(update_fields=['role'])
        return user

    def create_event(self, organizer, **overrides):
        defaults = {
            'title': 'Test event',
            'description': 'Test description',
            'event_type': 'community',
            'date': timezone.localdate() + timedelta(days=3),
            'location': 'Test location',
            'city': 'Moscow',
            'organizer': organizer,
            'max_volunteers': 2,
            'xp_reward': 50,
        }
        defaults.update(overrides)
        return Event.objects.create(**defaults)


class EventRegistrationFlowTests(BaseEventsTestCase):
    def test_reapply_after_cancelled_updates_existing_record(self):
        organizer = self.create_user('organizer1', role='organizer')
        volunteer = self.create_user('volunteer1', role='volunteer')
        event = self.create_event(organizer=organizer)

        existing = EventRegistration.objects.create(
            event=event,
            volunteer=volunteer,
            status='cancelled',
            message='Old message',
        )

        self.client.login(username=volunteer.username, password=self.password)
        response = self.client.post(
            reverse('event_register', kwargs={'pk': event.pk}),
            {'message': 'Updated message'},
        )

        self.assertRedirects(response, reverse('event_detail', kwargs={'pk': event.pk}))
        existing.refresh_from_db()
        self.assertEqual(EventRegistration.objects.filter(event=event, volunteer=volunteer).count(), 1)
        self.assertEqual(existing.status, 'pending')
        self.assertEqual(existing.message, 'Updated message')
        self.assertTrue(
            Notification.objects.filter(
                user=organizer,
                type='new_application',
                related_registration=existing,
            ).exists()
        )

    def test_cancel_approved_registration_removes_chat_membership(self):
        organizer = self.create_user('organizer_cancel_chat', role='organizer')
        volunteer = self.create_user('volunteer_cancel_chat', role='volunteer')
        event = self.create_event(organizer=organizer)
        EventRegistration.objects.create(
            event=event,
            volunteer=volunteer,
            status='approved',
        )
        channel = event.chat_channels.first()
        ChatChannelMembership.objects.get_or_create(channel=channel, user=volunteer)

        self.client.login(username=volunteer.username, password=self.password)
        response = self.client.post(reverse('event_cancel_registration', kwargs={'pk': event.pk}))

        self.assertRedirects(response, reverse('event_detail', kwargs={'pk': event.pk}))
        self.assertFalse(ChatChannelMembership.objects.filter(channel=channel, user=volunteer).exists())


class AuthenticationSecurityTests(BaseEventsTestCase):
    def test_login_ignores_external_next_redirect(self):
        user = self.create_user('volunteer2')
        response = self.client.post(
            f"{reverse('login')}?next=https://evil.example/phishing",
            {
                'username': user.username,
                'password': self.password,
                'next': 'https://evil.example/phishing',
            },
        )

        self.assertRedirects(response, reverse('event_list'))


class MutatingEndpointsMethodTests(BaseEventsTestCase):
    def test_event_delete_requires_post(self):
        organizer = self.create_user('organizer_delete_http', role='organizer')
        event = self.create_event(organizer=organizer)

        self.client.login(username=organizer.username, password=self.password)
        response = self.client.get(reverse('event_delete', kwargs={'pk': event.pk}))
        self.assertEqual(response.status_code, 405)

    def test_cancel_registration_requires_post(self):
        organizer = self.create_user('organizer2', role='organizer')
        volunteer = self.create_user('volunteer3', role='volunteer')
        event = self.create_event(organizer=organizer)
        EventRegistration.objects.create(event=event, volunteer=volunteer, status='pending')

        self.client.login(username=volunteer.username, password=self.password)
        response = self.client.get(reverse('event_cancel_registration', kwargs={'pk': event.pk}))
        self.assertEqual(response.status_code, 405)

    def test_mark_notification_read_requires_post(self):
        user = self.create_user('volunteer4')
        notification = Notification.objects.create(
            user=user,
            type='new_event',
            title='N',
            message='M',
        )

        self.client.login(username=user.username, password=self.password)
        response = self.client.get(reverse('notification_mark_read', kwargs={'pk': notification.pk}))
        self.assertEqual(response.status_code, 405)

    def test_logout_requires_post(self):
        user = self.create_user('volunteer7')
        self.client.login(username=user.username, password=self.password)
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 405)

    def test_logout_post_works(self):
        user = self.create_user('volunteer8')
        self.client.login(username=user.username, password=self.password)
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('event_list'))


class RegistrationManagementTests(BaseEventsTestCase):
    def test_approve_is_blocked_when_event_is_full(self):
        organizer = self.create_user('organizer3', role='organizer')
        approved_volunteer = self.create_user('volunteer5', role='volunteer')
        pending_volunteer = self.create_user('volunteer6', role='volunteer')
        event = self.create_event(organizer=organizer, max_volunteers=1)

        EventRegistration.objects.create(
            event=event,
            volunteer=approved_volunteer,
            status='approved',
        )
        pending_registration = EventRegistration.objects.create(
            event=event,
            volunteer=pending_volunteer,
            status='pending',
        )

        self.client.login(username=organizer.username, password=self.password)
        self.client.post(
            reverse('event_manage', kwargs={'pk': event.pk}),
            {
                'registration_id': pending_registration.pk,
                'action': 'approve',
            },
        )

        pending_registration.refresh_from_db()
        self.assertEqual(pending_registration.status, 'pending')

    def test_rejecting_approved_registration_removes_chat_membership(self):
        organizer = self.create_user('organizer_reject', role='organizer')
        volunteer = self.create_user('volunteer_reject', role='volunteer')
        event = self.create_event(organizer=organizer)
        registration = EventRegistration.objects.create(
            event=event,
            volunteer=volunteer,
            status='approved',
        )
        channel = event.chat_channels.first()
        ChatChannelMembership.objects.get_or_create(channel=channel, user=volunteer)
        self.assertTrue(ChatChannelMembership.objects.filter(channel=channel, user=volunteer).exists())

        self.client.login(username=organizer.username, password=self.password)
        response = self.client.post(
            reverse('event_manage', kwargs={'pk': event.pk}),
            {
                'registration_id': registration.pk,
                'action': 'reject',
            },
        )

        self.assertEqual(response.status_code, 200)
        registration.refresh_from_db()
        self.assertEqual(registration.status, 'rejected')
        self.assertFalse(ChatChannelMembership.objects.filter(channel=channel, user=volunteer).exists())

    def test_manage_with_missing_registration_id_is_graceful(self):
        organizer = self.create_user('organizer_missing_reg', role='organizer')
        event = self.create_event(organizer=organizer)

        self.client.login(username=organizer.username, password=self.password)
        response = self.client.post(
            reverse('event_manage', kwargs={'pk': event.pk}),
            {
                'action': 'approve',
            },
        )

        self.assertRedirects(response, reverse('event_manage', kwargs={'pk': event.pk}))


class AccessControlTests(BaseEventsTestCase):
    def test_volunteer_profile_requires_login(self):
        volunteer = self.create_user('volunteer9', role='volunteer')
        response = self.client.get(reverse('volunteer_profile', kwargs={'pk': volunteer.profile.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_volunteer_profile_forbidden_for_volunteer_role(self):
        volunteer = self.create_user('volunteer10', role='volunteer')
        self.client.login(username=volunteer.username, password=self.password)
        response = self.client.get(reverse('volunteer_profile', kwargs={'pk': volunteer.profile.pk}))
        self.assertRedirects(response, reverse('event_list'))

    def test_volunteer_profile_returns_404_for_non_volunteer_target(self):
        organizer = self.create_user('organizer5', role='organizer')
        organizer_target = self.create_user('organizer6', role='organizer')
        self.client.login(username=organizer.username, password=self.password)
        response = self.client.get(reverse('volunteer_profile', kwargs={'pk': organizer_target.profile.pk}))
        self.assertEqual(response.status_code, 404)


class EventLifecycleTests(BaseEventsTestCase):
    def test_organizer_can_soft_delete_event(self):
        organizer = self.create_user('organizer_delete', role='organizer')
        event = self.create_event(organizer=organizer)

        self.client.login(username=organizer.username, password=self.password)
        response = self.client.post(reverse('event_delete', kwargs={'pk': event.pk}))

        self.assertRedirects(response, reverse('my_events'))
        event.refresh_from_db()
        self.assertFalse(event.is_active)
        self.assertTrue(event.chat_channels.filter(is_archived=True).exists())

    def test_non_organizer_cannot_delete_event(self):
        organizer = self.create_user('organizer_delete_owner', role='organizer')
        volunteer = self.create_user('volunteer_delete_other', role='volunteer')
        event = self.create_event(organizer=organizer)

        self.client.login(username=volunteer.username, password=self.password)
        response = self.client.post(reverse('event_delete', kwargs={'pk': event.pk}))

        self.assertRedirects(response, reverse('event_detail', kwargs={'pk': event.pk}))
        event.refresh_from_db()
        self.assertTrue(event.is_active)

    def test_inactive_event_detail_and_register_return_404(self):
        organizer = self.create_user('organizer_inactive', role='organizer')
        volunteer = self.create_user('volunteer_inactive', role='volunteer')
        event = self.create_event(organizer=organizer, is_active=False)

        self.client.login(username=volunteer.username, password=self.password)
        detail_response = self.client.get(reverse('event_detail', kwargs={'pk': event.pk}))
        register_response = self.client.get(reverse('event_register', kwargs={'pk': event.pk}))

        self.assertEqual(detail_response.status_code, 404)
        self.assertEqual(register_response.status_code, 404)


class EventListAndTemplatesTests(BaseEventsTestCase):
    def test_event_list_invalid_date_filter_does_not_crash(self):
        response = self.client.get(reverse('event_list'), {'date_from': 'not-a-date'})
        self.assertEqual(response.status_code, 200)

    def test_event_create_page_renders_for_organizer(self):
        organizer = self.create_user('organizer4', role='organizer')
        self.client.login(username=organizer.username, password=self.password)
        response = self.client.get(reverse('event_create'))
        self.assertEqual(response.status_code, 200)


class NotificationsTests(BaseEventsTestCase):
    def test_notifications_list_has_pagination(self):
        user = self.create_user('volunteer11', role='volunteer')
        self.client.login(username=user.username, password=self.password)
        Notification.objects.bulk_create(
            [
                Notification(
                    user=user,
                    type='new_event',
                    title=f'Title {idx}',
                    message='Message',
                )
                for idx in range(25)
            ]
        )

        response = self.client.get(reverse('notifications_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['notifications']), 20)

        response_page_2 = self.client.get(reverse('notifications_list'), {'page': 2})
        self.assertEqual(response_page_2.status_code, 200)
        self.assertEqual(len(response_page_2.context['notifications']), 5)
