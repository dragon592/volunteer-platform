(function () {
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

    function setupMobileMenu() {
        const toggle = document.querySelector('[data-menu-toggle]');
        const menu = document.querySelector('[data-menu]');
        if (!toggle || !menu) {
            return;
        }

        toggle.addEventListener('click', function () {
            const expanded = toggle.getAttribute('aria-expanded') === 'true';
            toggle.setAttribute('aria-expanded', String(!expanded));
            menu.classList.toggle('open', !expanded);
        });
    }

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

    function showToast(text, type) {
        const root = document.getElementById('toast-root');
        if (!root) {
            return;
        }
        const toast = document.createElement('div');
        toast.className = 'toast ' + (type || 'info');
        const icon = type === 'error' ? '❌' : type === 'success' ? '✅' : type === 'warning' ? '⚠️' : 'ℹ️';
        toast.innerHTML = '<span>' + icon + '</span><div>' + text + '</div>';
        root.appendChild(toast);
        setTimeout(function () {
            toast.remove();
        }, 5000);
    }

    function setupChatAutoScroll() {
        const log = document.querySelector('[data-chat-log]');
        if (!log) {
            return;
        }
        log.scrollTop = log.scrollHeight;
    }

    function setupNotifications() {
        if (document.body.dataset.authenticated !== '1') {
            return;
        }

        const countUrl = document.body.dataset.notificationsCountUrl;
        const latestUrl = document.body.dataset.notificationsLatestUrl;
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

    document.addEventListener('DOMContentLoaded', function () {
        setupMobileMenu();
        setupPasswordToggles();
        setupChatAutoScroll();
        setupNotifications();

        // Expose CSRF helper for inline page scripts that still use fetch + POST.
        window.getCookie = getCookie;
    });
})();
