ACTIVE_REGISTRATION_STATUSES = ('pending', 'approved', 'completed')
APPROVED_REGISTRATION_STATUSES = ('approved', 'completed')
REAPPLY_REGISTRATION_STATUSES = ('rejected', 'cancelled')
REGISTRATION_ACTIONS = {'approve', 'reject', 'complete'}

# Уровни волонтёра
VOLUNTEER_LEVELS = [
    {'name': 'Beginner', 'min_xp': 0, 'icon': '🌱'},
    {'name': 'Helper', 'min_xp': 100, 'icon': '🤝'},
    {'name': 'Volunteer', 'min_xp': 300, 'icon': '⭐'},
    {'name': 'Leader', 'min_xp': 700, 'icon': '👑'},
]
