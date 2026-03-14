// =========================================
// Мобильное меню и UI функции
// =========================================

document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const menuToggle = document.querySelector('[data-menu-toggle]');
    const mainNav = document.querySelector('[data-menu]');
    const overlay = document.querySelector('[data-menu-overlay]');

    if (menuToggle && mainNav && overlay) {
        menuToggle.addEventListener('click', function() {
            const isExpanded = this.getAttribute('aria-expanded') === 'true';
            this.setAttribute('aria-expanded', !isExpanded);
            mainNav.classList.toggle('active');
            overlay.classList.toggle('active');
        });

        overlay.addEventListener('click', function() {
            menuToggle.setAttribute('aria-expanded', 'false');
            mainNav.classList.remove('active');
            overlay.classList.remove('active');
        });
    }

    // Password visibility toggle
    document.querySelectorAll('[data-toggle-password]').forEach(button => {
        button.addEventListener('click', function() {
            const inputId = this.getAttribute('data-toggle-password');
            const input = document.getElementById(inputId);
            if (input) {
                const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
                input.setAttribute('type', type);
                this.textContent = type === 'password' ? 'Показать' : 'Скрыть';
            }
        });
    });
});

// =========================================
// Уведомления и тосты
// =========================================

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showToast(message, type = 'info', duration = 5000) {
    const container = document.getElementById('toast-root');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    toast.innerHTML = `
        <span class="text-2xl">${icons[type] || icons.info}</span>
        <div class="flex-1">
            <p class="text-gray-800 font-medium">${message}</p>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
        </button>
    `;

    container.appendChild(toast);

    if (duration > 0) {
        setTimeout(() => {
            toast.classList.add('hiding');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
}

//Notification polling
function updateNotificationCount() {
    const countUrl = document.body.getAttribute('data-notifications-count-url');
    if (!countUrl) return;

    fetch(countUrl, { credentials: 'same-origin' })
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('notification-count');
            if (badge) {
                if (data.count > 0) {
                    badge.textContent = data.count > 99 ? '99+' : data.count;
                    badge.hidden = false;
                } else {
                    badge.hidden = true;
                }
            }
        })
        .catch(err => console.error('Error loading notifications:', err));
}

let lastNotificationId = null;
function checkNewNotifications() {
    const latestUrl = document.body.getAttribute('data-notifications-latest-url');
    if (!latestUrl) return;

    fetch(latestUrl, { credentials: 'same-origin' })
        .then(response => response.json())
        .then(data => {
            if (data.notifications && data.notifications.length > 0) {
                const latest = data.notifications[0];
                if (lastNotificationId !== latest.id) {
                    lastNotificationId = latest.id;
                    const typeMap = {
                        'application_approved': 'success',
                        'application_rejected': 'error',
                        'new_application': 'info',
                        'new_event': 'info',
                        'event_reminder': 'warning'
                    };
                    showToast(latest.title + ': ' + latest.message, typeMap[latest.type] || 'info');
                }
            }
            updateNotificationCount();
        })
        .catch(err => console.error('Error checking notifications:', err));
}

// Initialize notifications if authenticated
if (document.body.getAttribute('data-authenticated') === '1') {
    updateNotificationCount();
    setInterval(checkNewNotifications, 30000);
    setTimeout(checkNewNotifications, 2000);
}
