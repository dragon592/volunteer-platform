from .views_auth import login_view, logout_view, register_view
from .views_chat import chat_channel_detail, chat_channels, chat_create_channel
from .views_events import (
    event_cancel_registration,
    event_create,
    event_detail,
    event_edit,
    event_list,
    event_manage_registrations,
    event_register,
    my_events,
)
from .views_notifications import (
    notification_mark_all_read,
    notification_mark_read,
    notifications_latest,
    notifications_list,
    notifications_unread_count,
)
from .views_profiles import profile_view, volunteer_profile, volunteer_search

__all__ = [
    'event_list',
    'event_detail',
    'event_create',
    'event_edit',
    'event_register',
    'event_cancel_registration',
    'event_manage_registrations',
    'register_view',
    'login_view',
    'logout_view',
    'profile_view',
    'my_events',
    'volunteer_search',
    'volunteer_profile',
    'notifications_list',
    'notification_mark_read',
    'notification_mark_all_read',
    'notifications_unread_count',
    'notifications_latest',
    'chat_channels',
    'chat_channel_detail',
    'chat_create_channel',
]
