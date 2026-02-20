from django.core.management.base import BaseCommand
from events.models import Skill


class Command(BaseCommand):
    help = 'Creates initial skills data'

    def handle(self, *args, **options):
        skills = [
            ('Экология', '🌱'),
            ('Медицина', '🏥'),
            ('Образование', '📚'),
            ('Социальная помощь', '🤝'),
            ('Спорт', '⚽'),
            ('Культура', '🎭'),
            ('IT и технологии', '💻'),
            ('Строительство', '🏗️'),
            ('Животные', '🐾'),
            ('Дети', '👶'),
            ('Пожилые люди', '👴'),
            ('Инвалиды', '♿'),
            ('Переводы', '🌍'),
            ('Фотография', '📷'),
            ('Дизайн', '🎨'),
        ]
        
        created_count = 0
        for name, icon in skills:
            skill, created = Skill.objects.get_or_create(
                name=name,
                defaults={'icon': icon}
            )
            if created:
                created_count += 1
                self.stdout.write(f'  Created: {name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} skills')
        )

