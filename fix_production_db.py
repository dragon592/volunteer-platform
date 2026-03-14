#!/usr/bin/env python
"""
Скрипт для диагностики и исправления проблем с базой данных в production.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'volunteer.settings')
django.setup()

from django.db import connection
from django.core.management import call_command

print('=' * 60)
print('DIAGNOSTIC: Production Database')
print('=' * 60)

# 1. Проверяем, какая база используется
print(f'\n1. Database ENGINE: {connection.settings_dict["ENGINE"]}')
print(f'   Database NAME: {connection.settings_dict["NAME"]}')

# 2. Проверяем существование таблицы events_event
with connection.cursor() as cursor:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events_event'")
    table_exists = cursor.fetchone() is not None
    print(f'\n2. Table "events_event" exists: {table_exists}')

    if not table_exists:
        print('\n   [ERROR] Table events_event is missing!')
        print('   This means migrations were not applied correctly.')

# 3. Проверяем статус миграций
print('\n3. Checking migration status...')
try:
    from django.db.migrations.executor import MigrationExecutor
    executor = MigrationExecutor(connection)
    migration_records = executor.loader.graph.leaf_nodes()
    print(f'   Applied migrations: {len(executor.loader.applied_migrations)}')
    print(f'   Pending migrations: {len(executor.loader.pending_migrations)}')
    
    if executor.loader.pending_migrations:
        print('\n   [WARNING] Pending migrations detected:')
        for app, migration in executor.loader.pending_migrations:
            print(f'      - {app}.{migration}')
except Exception as e:
    print(f'   [ERROR] Could not check migrations: {e}')

# 4. Предлагаем решение
if not table_exists:
    print('\n4. Attempting to fix...')
    try:
        print('   Running: python manage.py migrate --noinput')
        call_command('migrate', '--noinput', verbosity=2)
        print('   [SUCCESS] Migrations applied!')
        
        # Проверяем снова
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events_event'")
            table_exists_after = cursor.fetchone() is not None
            print(f'   Table exists after migrate: {table_exists_after}')
    except Exception as e:
        print(f'   [ERROR] Migration failed: {e}')
        print('\n   Manual steps required:')
        print('   1. Delete the SQLite database file (db.sqlite3)')
        print('   2. Run: python manage.py migrate --noinput')
        print('   3. Run: python manage.py collectstatic --noinput --clear')
        print('   4. Restart the application')
else:
    print('\n4. Database is healthy. No action needed.')

print('\n' + '=' * 60)
print('Diagnostic complete.')
print('=' * 60)