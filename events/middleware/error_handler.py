"""
Глобальный middleware для обработки ошибок.
Централизованная обработка исключений и возврат корректных HTTP ответов.
"""
import logging
import traceback
from django.http import JsonResponse, HttpResponseServerError
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(MiddlewareMixin):
    """
    Обрабатывает все необработанные исключения и возвращает корректные ответы.
    В режиме DEBUG возвращает подробную информацию, в production - общее сообщение.
    """
    
    def process_exception(self, request, exception):
        # Логируем ошибку с полным трейсбэком
        logger.error(
            f"Unhandled exception in {request.path}: {str(exception)}",
            exc_info=True,
            extra={
                'request': request,
                'exception': exception,
                'traceback': traceback.format_exc(),
            }
        )
        
        # Если это AJAX запрос или API endpoint - возвращаем JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.path.startswith('/api/'):
            return self._json_error_response(request, exception)
        
        # Для обычных запросов возвращаем HTML страницу с ошибкой
        return self._html_error_response(request, exception)
    
    def _json_error_response(self, request, exception):
        """Возвращает JSON ответ с информацией об ошибке"""
        from django.conf import settings
        
        data = {
            'success': False,
            'error': {
                'message': str(exception),
                'type': exception.__class__.__name__,
            }
        }
        
        # В DEBUG режиме добавляем трейсбэк
        if settings.DEBUG:
            data['error']['traceback'] = traceback.format_exc()
            data['error']['debug'] = True
        
        status_code = self._get_http_status_code(exception)
        return JsonResponse(data, status=status_code)
    
    def _html_error_response(self, request, exception):
        """Возвращает HTML страницу с ошибкой"""
        from django.conf import settings
        
        status_code = self._get_http_status_code(exception)
        
        if settings.DEBUG:
            # В DEBUG показываем стандартную страницу ошибки Django
            return HttpResponseServerError()
        else:
            # В production показываем кастомную страницу
            # Можно создать шаблон 500.html
            return HttpResponseServerError(
                '<h1>Произошла ошибка</h1><p>Пожалуйста, попробуйте позже.</p>'
            )
    
    def _get_http_status_code(self, exception):
        """Определяет HTTP статус код на основе типа исключения"""
        from django.core.exceptions import (
            PermissionDenied, ObjectDoesNotExist, ValidationError,
            SuspiciousOperation, Http404
        )
        
        mapping = {
            Http404: 404,
            PermissionDenied: 403,
            ValidationError: 400,
            SuspiciousOperation: 400,
        }
        
        for exc_type, status_code in mapping.items():
            if isinstance(exception, exc_type):
                return status_code
        
        # По умолчанию 500
        return 500


def get_client_ip(request):
    """
    Получает IP адрес клиента с учетом прокси.
    Использует HTTP_X_FORWARDED_FOR если доступен, иначе REMOTE_ADDR.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Берем первый IP из списка (клиент)
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip
