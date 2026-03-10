#!/usr/bin/env python
"""
Экспорт данных из SQLite в JSON с кодировкой UTF-8
Используется для переноса данных на Render.com
"""
import os
import sys
import json
import io
from pathlib import Path

# Добавляем путь к проекту
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'volunteer.settings')

import django
django.setup()

from django.core.management import call_command

# Для Windows: устанавливаем кодировку UTF-8 для stdout
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def export_data(output_file='data_dump.json'):
    """Экспорт всех данных в JSON файл с UTF-8 кодировкой"""
    print(f"Экспорт данных в {output_file}...")
    
    try:
        # Вызываем dumpdata с правильными параметрами
        with open(output_file, 'w', encoding='utf-8') as f:
            # Перенаправляем вывод в файл
            call_command(
                'dumpdata',
                '--natural-foreign',
                '--natural-primary',
                exclude=['contenttypes', 'auth.Permission'],
                indent=2,
                stdout=f
            )
        
        # Проверяем размер файла
        file_size = os.path.getsize(output_file) / 1024
        print(f"✅ Данные успешно экспортированы в {output_file} ({file_size:.2f} KB)")
        
        # Показываем пример содержимого
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"📊 Экспортировано объектов: {len(data)}")
            
            # Группируем по моделям
            models_count = {}
            for item in data:
                model = item.get('model', 'unknown')
                models_count[model] = models_count.get(model, 0) + 1
            
            print("\n📋 Статистика по моделям:")
            for model, count in sorted(models_count.items()):
                print(f"  {model}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при экспорте: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    output = 'data_dump.json'
    if len(sys.argv) > 1:
        output = sys.argv[1]
    
    success = export_data(output)
    sys.exit(0 if success else 1)