"""
Кастомный обработчик исключений для Django REST Framework.
"""
import logging

logger = logging.getLogger(__name__)

# Безопасный импорт DRF
try:
    from rest_framework.views import exception_handler
    from rest_framework.response import Response
    from rest_framework import status
    DRF_AVAILABLE = True
except ImportError:
    DRF_AVAILABLE = False
    exception_handler = None


def custom_exception_handler(exc, context):
    """
    Кастомный обработчик исключений DRF.
    Логирует ошибки и возвращает структурированный JSON ответ.
    """
    # Если DRF не установлен, возвращаем None
    if not DRF_AVAILABLE:
        return None
    
    # Сначала вызываем стандартный обработчик
    response = exception_handler(exc, context)
    
    # Логируем ошибку
    view = context.get('view')
    view_name = view.__class__.__name__ if view else 'Unknown'
    logger.error(
        f"API error in {view_name}: {str(exc)}",
        exc_info=True,
        extra={
            'view': view_name,
            'request': context.get('request'),
            'exception': exc,
        }
    )
    
    if response is not None:
        # Кастомизируем ответ
        custom_response_data = {
            'success': False,
            'error': {
                'message': str(exc),
                'type': exc.__class__.__name__,
                'details': response.data if hasattr(response, 'data') else {}
            }
        }
        response.data = custom_response_data
    
    return response
