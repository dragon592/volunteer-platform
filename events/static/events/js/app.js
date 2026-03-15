(function () {
    // =========================================
    // Cookie helper
    // =========================================
    function getCookie(name) {
        const cookies = document.cookie ? document.cookie.split(';') : [];
        for (const rawCookie of cookies) {
            const cookie = rawCookie.trim();
            if (cookie.startsWith(name + '=')) {
                return decodeURIComponent(cookie.slice(name.length + 1));
            }
        }
        return null;
    }

    // =========================================
    // Mobile menu toggle
    // =========================================
    function setupMobileMenu() {
        const toggle = document.querySelector('[data-menu-toggle]');
        const menu = document.querySelector('[data-menu]');
        const overlay = document.querySelector('[data-menu-overlay]');
        if (!toggle || !menu || !overlay) {
            return;
        }

        toggle.addEventListener('click', function () {
            const isExpanded = toggle.getAttribute('aria-expanded') === 'true';
            toggle.setAttribute('aria-expanded', !isExpanded);
            menu.classList.toggle('active');
            overlay.classList.toggle('active');
        });

        overlay.addEventListener('click', function () {
            toggle.setAttribute('aria-expanded', 'false');
            menu.classList.remove('active');
            overlay.classList.remove('active');
        });
    }

    // =========================================
    // Password visibility toggle
    // =========================================
    function setupPasswordToggles() {
        document.querySelectorAll('[data-toggle-password]').forEach(function (button) {
            button.addEventListener('click', function () {
                const targetId = button.getAttribute('data-toggle-password');
                const field = document.getElementById(targetId);
                if (!field) {
                    return;
                }
                const show = field.type === 'password';
                field.type = show ? 'text' : 'password';
                button.textContent = show ? 'Скрыть' : 'Показать';
            });
        });
    }

    // =========================================
    // Toast notifications
    // =========================================
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

    // =========================================
    // Chat auto-scroll
    // =========================================
    function setupChatAutoScroll() {
        const log = document.querySelector('[data-chat-log]');
        if (!log) {
            return;
        }
        log.scrollTop = log.scrollHeight;
    }

    // =========================================
    // Notifications polling
    // =========================================
    function setupNotifications() {
        if (document.body.getAttribute('data-authenticated') !== '1') {
            return;
        }

        const countUrl = document.body.getAttribute('data-notifications-count-url');
        const latestUrl = document.body.getAttribute('data-notifications-latest-url');
        const badge = document.getElementById('notification-count');
        if (!latestUrl || !badge) {
            return;
        }

        function renderCount(count) {
            if (count > 0) {
                badge.hidden = false;
                badge.textContent = count > 99 ? '99+' : String(count);
            } else {
                badge.hidden = true;
            }
        }

        function updateCountFallback() {
            if (!countUrl) {
                return Promise.resolve();
            }
            return fetch(countUrl, { credentials: 'same-origin' })
                .then(function (response) {
                    if (!response.ok) {
                        throw new Error('Notifications count request failed');
                    }
                    return response.json();
                })
                .then(function (data) {
                    renderCount(data.count || 0);
                })
                .catch(function () {});
        }

        function checkLatest() {
            if (document.hidden) {
                return;
            }
            fetch(latestUrl, { credentials: 'same-origin' })
                .then(function (response) {
                    if (!response.ok) {
                        throw new Error('Notifications latest request failed');
                    }
                    return response.json();
                })
                .then(function (data) {
                    renderCount(data.count || 0);
                    if (!data.notifications || !data.notifications.length) {
                        return;
                    }

                    const latest = data.notifications[0];
                    const previousId = sessionStorage.getItem('lastNotificationId');
                    if (previousId !== String(latest.id)) {
                        sessionStorage.setItem('lastNotificationId', String(latest.id));
                        const typeMap = {
                            application_approved: 'success',
                            application_rejected: 'error',
                            new_application: 'info',
                            new_event: 'info',
                            event_reminder: 'warning',
                            new_message: 'info',
                            achievement_unlocked: 'success',
                            level_up: 'success',
                        };
                        showToast(latest.title + ': ' + latest.message, typeMap[latest.type] || 'info');
                    }
                })
                .catch(function () {
                    updateCountFallback();
                });
        }

        checkLatest();
        setInterval(checkLatest, 30000);
    }

    // =========================================
    // Form helpers
    // =========================================
    function setupFormEnhancements() {
        // Auto-hide success messages after 5 seconds
        const successMessages = document.querySelectorAll('.flash-success, .messages .success');
        successMessages.forEach(function (msg) {
            setTimeout(() => {
                msg.style.transition = 'opacity 0.5s';
                msg.style.opacity = '0';
                setTimeout(() => msg.remove(), 500);
            }, 5000);
        });
    }

    // =========================================
    // Initialize
    // =========================================
    document.addEventListener('DOMContentLoaded', function () {
        setupMobileMenu();
        setupPasswordToggles();
        setupChatAutoScroll();
        setupNotifications();
        setupFormEnhancements();

        // Expose CSRF helper for inline page scripts
        window.getCookie = getCookie;
    });
})();
