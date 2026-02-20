from django.urls import path

from . import views

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
    path('events/create/', views.event_create, name='event_create'),
    path('events/<int:pk>/edit/', views.event_edit, name='event_edit'),
    path('events/<int:pk>/register/', views.event_register, name='event_register'),
    path('events/<int:pk>/cancel/', views.event_cancel_registration, name='event_cancel_registration'),
    path('events/<int:pk>/manage/', views.event_manage_registrations, name='event_manage'),
    path('events/<int:event_pk>/chat/create-channel/', views.chat_create_channel, name='chat_create_channel'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('my-events/', views.my_events, name='my_events'),
    path('volunteers/', views.volunteer_search, name='volunteer_search'),
    path('volunteers/<int:pk>/', views.volunteer_profile, name='volunteer_profile'),
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<int:pk>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/mark-all-read/', views.notification_mark_all_read, name='notification_mark_all_read'),
    path('api/notifications/count/', views.notifications_unread_count, name='notifications_unread_count'),
    path('api/notifications/latest/', views.notifications_latest, name='notifications_latest'),
    path('chat/', views.chat_channels, name='chat_channels'),
    path('chat/<int:channel_id>/', views.chat_channel_detail, name='chat_channel_detail'),
]
