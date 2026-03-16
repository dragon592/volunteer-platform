/**
 * API Service - единый клиент для всех API запросов
 * Обрабатывает ошибки, CSRF токены, авторизацию
 */

const API_BASE_URL = window.location.origin;

/**
 * Получает CSRF токен из cookies
 */
function getCSRFToken() {
    const name = 'csrftoken';
    const cookies = document.cookie ? document.cookie.split(';') : [];
    for (const cookie of cookies) {
        const c = cookie.trim();
        if (c.startsWith(name + '=')) {
            return decodeURIComponent(c.slice(name.length + 1));
        }
    }
    return null;
}

/**
 * Универсальная функция для выполнения API запросов
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const csrfToken = getCSRFToken();
    
    const defaultHeaders = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    };
    
    if (csrfToken) {
        defaultHeaders['X-CSRFToken'] = csrfToken;
    }
    
    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers,
        },
        credentials: 'include', // Включаем куки
    };
    
    try {
        const response = await fetch(url, config);
        
        // Проверяем статус ответа
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const error = new Error(errorData.error?.message || `HTTP ${response.status}: ${response.statusText}`);
            error.status = response.status;
            error.data = errorData;
            throw error;
        }
        
        // Парсим JSON если есть контент
        const contentLength = response.headers.get('content-length');
        if (contentLength && contentLength === '0') {
            return null;
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Request failed:', error);
        throw error;
    }
}

/**
 * API для событий
 */
const EventAPI = {
    // Получить список событий
    async getEvents(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = queryString ? `/events/?${queryString}` : '/events/';
        return apiRequest(endpoint);
    },
    
    // Получить детали события
    async getEvent(eventId) {
        return apiRequest(`/events/${eventId}/`);
    },
    
    // Создать событие
    async createEvent(formData) {
        return apiRequest('/events/create/', {
            method: 'POST',
            body: JSON.stringify(formData),
        });
    },
    
    // Обновить событие
    async updateEvent(eventId, formData) {
        return apiRequest(`/events/${eventId}/edit/`, {
            method: 'POST',
            body: JSON.stringify(formData),
        });
    },
    
    // Удалить событие
    async deleteEvent(eventId) {
        return apiRequest(`/events/${eventId}/delete/`, {
            method: 'POST',
        });
    },
    
    // Зарегистрироваться на событие
    async registerForEvent(eventId, message = '') {
        return apiRequest(`/events/${eventId}/register/`, {
            method: 'POST',
            body: JSON.stringify({ message }),
        });
    },
    
    // Отменить регистрацию
    async cancelRegistration(eventId) {
        return apiRequest(`/events/${eventId}/cancel/`, {
            method: 'POST',
        });
    },
    
    // Управление регистрациями (для организаторов)
    async manageRegistration(registrationId, status) {
        return apiRequest(`/events/registrations/${registrationId}/manage/`, {
            method: 'POST',
            body: JSON.stringify({ status }),
        });
    },
};

/**
 * API для профилей
 */
const ProfileAPI = {
    // Получить свой профиль
    async getMyProfile() {
        return apiRequest('/profile/');
    },
    
    // Обновить профиль
    async updateProfile(formData) {
        return apiRequest('/profile/', {
            method: 'POST',
            body: JSON.stringify(formData),
        });
    },
    
    // Поиск волонтеров
    async searchVolunteers(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return apiRequest(`/volunteers/?${queryString}`);
    },
    
    // Получить профиль волонтера
    async getVolunteerProfile(volunteerId) {
        return apiRequest(`/volunteers/${volunteerId}/`);
    },
    
    // Получить таблицу лидеров
    async getLeaderboard() {
        return apiRequest('/leaderboard/');
    },
};

/**
 * API для уведомлений
 */
const NotificationAPI = {
    // Получить список уведомлений
    async getNotifications(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return apiRequest(`/notifications/?${queryString}`);
    },
    
    // Отметить как прочитанное
    async markAsRead(notificationId) {
        return apiRequest(`/notifications/${notificationId}/read/`, {
            method: 'POST',
        });
    },
    
    // Отметить все как прочитанные
    async markAllAsRead() {
        return apiRequest('/notifications/mark-all-read/', {
            method: 'POST',
        });
    },
    
    // Получить количество непрочитанных
    async getUnreadCount() {
        return apiRequest('/api/notifications/count/');
    },
    
    // Получить последние уведомления
    async getLatestNotifications() {
        return apiRequest('/api/notifications/latest/');
    },
};

/**
 * API для чата
 */
const ChatAPI = {
    // Получить список каналов
    async getChannels() {
        return apiRequest('/chat/');
    },
    
    // Получить детали канала
    async getChannel(channelId) {
        return apiRequest(`/chat/${channelId}/`);
    },
    
    // Отправить сообщение
    async sendMessage(channelId, content) {
        return apiRequest(`/chat/${channelId}/`, {
            method: 'POST',
            body: JSON.stringify({ content }),
        });
    },
    
    // Создать канал (для организаторов)
    async createChannel(eventId, name, description = '') {
        return apiRequest(`/events/${eventId}/chat/create-channel/`, {
            method: 'POST',
            body: JSON.stringify({ name, description }),
        });
    },
};

/**
 * API для аутентификации
 */
const AuthAPI = {
    // Регистрация
    async register(userData) {
        return apiRequest('/register/', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
    },
    
    // Вход
    async login(credentials) {
        return apiRequest('/login/', {
            method: 'POST',
            body: JSON.stringify(credentials),
        });
    },
    
    // Выход
    async logout() {
        return apiRequest('/logout/', {
            method: 'POST',
        });
    },
};

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        EventAPI,
        ProfileAPI,
        NotificationAPI,
        ChatAPI,
        AuthAPI,
    };
}
