import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'volunteer.settings')
django.setup()

from django.db import connection

print('Database:', connection.settings_dict['NAME'])
with connection.cursor() as cursor:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events_event'")
    result = cursor.fetchone()
    print('Table exists:', result is not None)
    if result:
        print('Table info:', result)