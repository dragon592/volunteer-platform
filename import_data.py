#!/usr/bin/env python
"""
Импорт данных в PostgreSQL (Render.com)
Используется после деплоя для загрузки данных из дампа
"""
import os
import sys
import json
from pathlib import Path

# Добавляем путь к проекту
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'volunteer.settings')

import django
django.setup()

from django.core.management import call_command
from django.db.models.signals import post_save
from events.models import ChatChannel

# Отключаем сигнал post_save для Event, который создаёт ChatChannel
post_save.disconnect(receiver=ChatChannel.create_default_event_channel, sender='events.Event')

def import_data(data_file='data_dump.json'):
    """Импорт данных из JSON файла"""
    print(f"Импорт данных из {data_file}...")
    
    try:
        # Проверяем существование файла
        if not os.path.exists(data_file):
            print(f"❌ Файл {data_file} не найден!")
            return False
        
        # Проверяем размер файла
        file_size = os.path.getsize(data_file) / 1024
        print(f"📦 Размер файла: {file_size:.2f} KB")
        
        # Загружаем данные
        call_command('loaddata', data_file)
        
        print(f"✅ Данные успешно импортированы!")
        
        # Показываем статистику
        from events.models import Event, UserProfile, Achievement, ChatChannel, Skill
        print("\n📊 Текущее состояние базы данных:")
        print(f"  Пользователи: {UserProfile.objects.count()}")
        print(f"  События: {Event.objects.count()}")
        print(f"  Достижения: {Achievement.objects.count()}")
        print(f"  Каналы чата: {ChatChannel.objects.count()}")
        print(f"  Навыки: {Skill.objects.count()}")
        
        # Включаем сигнал обратно после импорта
        post_save.connect(receiver=ChatChannel.create_default_event_channel, sender='events.Event')
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при импорте: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    data_file = 'data_dump.json'
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    
    success = import_data(data_file)
    sys.exit(0 if success else 1)