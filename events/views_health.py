from django.http import JsonResponse
from django.db import connection


def health_check(request):
    """
    Health check endpoint for Render and other hosting platforms.
    Returns 200 OK if the application is healthy.
    """
    try:
        # Проверяем подключение к базе данных
        connection.ensure_connection()
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'

    status_code = 200 if db_status == 'healthy' else 503

    return JsonResponse({
        'status': db_status,
        'service': 'volunteer-platform',
    }, status=status_code)
