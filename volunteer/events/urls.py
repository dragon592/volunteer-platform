from django.urls import path
from .views import event_list

urlpatterns = [
    path('', event_list, name='event_list'),
]