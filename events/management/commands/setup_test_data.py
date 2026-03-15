#!/usr/bin/env python
"""Создание тестовых данных для разработки"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from events.models import UserProfile, Event, Skill, EventRegistration, ChatChannel, Achievement, VolunteerAchievement
from django.utils import timezone
from datetime import timedelta, date

class Command(BaseCommand):
    help = 'Создает тестовые данные для разработки'

    def handle(self, *args, **options):
        self.stdout.write('Создание тестовых данных...')

        # Создаем навыки
        skills_data = [
            'Программирование', 'Дизайн', 'Маркетинг', 'Копирайтинг',
            'Организация мероприятий', 'Фотография', 'Видеосъемка',
            'Перевод', 'Соцсети', 'Администрирование'
        ]
        skills = []
        for skill_name in skills_data:
            skill, created = Skill.objects.get_or_create(name=skill_name)
            skills.append(skill)
            if created:
                self.stdout.write(f'  [OK] Создан навык: {skill_name}')

        # Создаем достижения
        achievements_data = [
            ('Первые шаги', 'Создайте первый профиль', '🎯', 'profile'),
            ('Первый ивент', 'Создайте первое событие', '📅', 'event'),
            ('Волонтер', 'Зарегистрируйтесь на событие', '🤝', 'registration'),
            ('Помощник', 'Помогите 5 событиям', '🛠️', 'help'),
            ('Лидер', 'Создайте 3 события', '👑', 'leader'),
        ]
        for title, desc, icon, cat in achievements_data:
            ach, created = Achievement.objects.get_or_create(
                title=title,
                defaults={
                    'description': desc,
                    'icon': icon,
                    'category': cat,
                    'is_active': True,
                    'slug': title.lower().replace(' ', '-')
                }
            )
            if created:
                self.stdout.write(f'  [OK] Создано достижение: {title}')

        # Создаем тестовых пользователей
        users_data = [
            {'username': 'volunteer1', 'email': 'volunteer1@test.com', 'first_name': 'Иван', 'last_name': 'Петров', 'role': 'volunteer'},
            {'username': 'volunteer2', 'email': 'volunteer2@test.com', 'first_name': 'Мария', 'last_name': 'Сидорова', 'role': 'volunteer'},
            {'username': 'organizer1', 'email': 'organizer1@test.com', 'first_name': 'Алексей', 'last_name': 'Смирнов', 'role': 'organizer'},
            {'username': 'organizer2', 'email': 'organizer2@test.com', 'first_name': 'Елена', 'last_name': 'Кузнецова', 'role': 'organizer'},
        ]

        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                }
            )
            if created:
                user.set_password('test123456')
                user.save()
                profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'role': user_data['role']})
                self.stdout.write(f'  [OK] Создан пользователь: {user.username} ({user_data["role"]})')
            else:
                # Убедимся, что у пользователя есть профиль
                profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'role': user_data['role']})

        # Создаем события
        organizer = User.objects.get(username='organizer1')
        events_data = [
            {
                'title': 'Экологический субботник',
                'description': 'Помощь в уборке парка, посадка деревьев. Нужны активные и ответственные волонтеры.',
                'location': 'Центральный парк',
                'city': 'Алматы',
                'date': timezone.localdate() + timedelta(days=7),
                'time': '10:00',
                'event_type': 'one_time',
                'max_volunteers': 20,
                'xp_reward': 50,
                'skills': ['Организация мероприятий', 'Фотография'],
            },
            {
                'title': 'Онлайн-марафон по программированию',
                'description': '24-часовой хакатон для начинающих. Нужны наставники и участники.',
                'location': 'Online',
                'city': 'Онлайн',
                'date': timezone.localdate() + timedelta(days=14),
                'time': '18:00',
                'event_type': 'online',
                'max_volunteers': 50,
                'xp_reward': 100,
                'skills': ['Программирование', 'Администрирование'],
            },
            {
                'title': 'Фестиваль искусств',
                'description': 'Помощь в организации фестиваля: регистрация, навигация, работа с гостями.',
                'location': 'Культурный центр',
                'city': 'Нур-Султан',
                'date': timezone.localdate() + timedelta(days=21),
                'time': '11:00',
                'event_type': 'recurring',
                'max_volunteers': 30,
                'xp_reward': 75,
                'skills': ['Организация мероприятий', 'Соцсети', 'Фотография'],
            },
            {
                'title': 'Помощь в приюте для животных',
                'description': 'Выгул собак, уход за животными, помощь в администрировании.',
                'location': 'Приют "Добрые сердца"',
                'city': 'Шымкент',
                'date': timezone.localdate() + timedelta(days=3),
                'time': '09:00',
                'event_type': 'one_time',
                'max_volunteers': 15,
                'xp_reward': 40,
                'skills': ['Организация мероприятий'],
            },
            {
                'title': 'Мастер-класс по дизайну',
                'description': 'Проведение мастер-класса по основам графического дизайна для начинающих.',
                'location': 'Коворкинг "Старт"',
                'city': 'Караганда',
                'date': timezone.localdate() + timedelta(days=10),
                'time': '14:00',
                'event_type': 'online',
                'max_volunteers': 25,
                'xp_reward': 60,
                'skills': ['Дизайн', 'Копирайтинг'],
            },
        ]

        for event_data in events_data:
            event, created = Event.objects.get_or_create(
                title=event_data['title'],
                organizer=organizer,
                defaults={
                    'description': event_data['description'],
                    'location': event_data['location'],
                    'city': event_data['city'],
                    'date': event_data['date'],
                    'time': event_data['time'],
                    'event_type': event_data['event_type'],
                    'max_volunteers': event_data['max_volunteers'],
                    'xp_reward': event_data['xp_reward'],
                }
            )
            if created:
                # Добавляем навыки
                for skill_name in event_data['skills']:
                    skill = Skill.objects.get(name=skill_name)
                    event.required_skills.add(skill)
                self.stdout.write(f'  [OK] Создано событие: {event.title}')

        # Создаем регистрации на события
        volunteer_user = User.objects.get(username='volunteer1')
        event = Event.objects.first()
        if event:
            reg, created = EventRegistration.objects.get_or_create(
                event=event,
                volunteer=volunteer_user,
                defaults={'status': 'approved'}
            )
            if created:
                self.stdout.write(f'  [OK] Создана регистрация: {volunteer_user.username} на {event.title}')

        # Создаем каналы чата для событий
        for event in Event.objects.all()[:3]:
            channel, created = ChatChannel.objects.get_or_create(
                event=event,
                defaults={'name': f'Чат: {event.title}'}
            )
            if created:
                self.stdout.write(f'  [OK] Создан канал: {channel.name}')

        # Создаем волонтерские достижения
        for user in User.objects.all():
            try:
                profile = UserProfile.objects.get(user=user)
                for achievement in Achievement.objects.all()[:2]:
                    va, created = VolunteerAchievement.objects.get_or_create(
                        volunteer=user,
                        achievement=achievement,
                        defaults={'awarded_at': timezone.now()}
                    )
                    if created:
                        self.stdout.write(f'  [OK] {user.username} получил достижение: {achievement.title}')
            except UserProfile.DoesNotExist:
                pass

        self.stdout.write(self.style.SUCCESS('\n[SUCCESS] Тестовые данные созданы успешно!'))
        self.stdout.write(f'\nСтатистика:')
        self.stdout.write(f'  Пользователей: {User.objects.count()}')
        self.stdout.write(f'  Профилей: {UserProfile.objects.count()}')
        self.stdout.write(f'  Событий: {Event.objects.count()}')
        self.stdout.write(f'  Навыков: {Skill.objects.count()}')
        self.stdout.write(f'  Регистраций: {EventRegistration.objects.count()}')
        self.stdout.write(f'  Каналов чата: {ChatChannel.objects.count()}')
        self.stdout.write(f'  Достижений: {Achievement.objects.count()}')
        self.stdout.write('\nТестовые пароли: test123456')
        self.stdout.write('Перейдите на http://127.0.0.1:8000/ и войдите в систему')
