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
    
        // Ensure menu starts closed
        menu.classList.remove('active');
        overlay.classList.remove('active');
        toggle.setAttribute('aria-expanded', 'false');
    
        toggle.addEventListener('click', function (e) {
            e.stopPropagation();
            const isExpanded = toggle.getAttribute('aria-expanded') === 'true';
            const newState = !isExpanded;
            toggle.setAttribute('aria-expanded', newState);
            
            if (newState) {
                menu.classList.add('active');
                overlay.classList.add('active');
                // Prevent body scroll when menu is open
                document.body.style.overflow = 'hidden';
            } else {
                menu.classList.remove('active');
                overlay.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    
        overlay.addEventListener('click', function () {
            toggle.setAttribute('aria-expanded', 'false');
            menu.classList.remove('active');
            overlay.classList.remove('active');
            document.body.style.overflow = '';
        });
    
        // Close menu when clicking on a link
        menu.addEventListener('click', function (e) {
            if (e.target.tagName === 'A' && !e.target.hasAttribute('data-menu-toggle')) {
                toggle.setAttribute('aria-expanded', 'false');
                menu.classList.remove('active');
                overlay.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    
        // Close menu on escape key
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
                toggle.setAttribute('aria-expanded', 'false');
                menu.classList.remove('active');
                overlay.classList.remove('active');
                document.body.style.overflow = '';
            }
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
                button.setAttribute('aria-label', show ? 'Скрыть пароль' : 'Показать пароль');
                
                // Add subtle animation
                field.style.transition = 'all 0.2s ease';
                field.style.boxShadow = show ? '0 0 0 4px rgba(28, 110, 91, 0.12)' : '';
                setTimeout(() => {
                    field.style.boxShadow = '';
                }, 200);
            });
        });
    }

    // =========================================
    // Auth page animations
    // =========================================
    function setupAuthAnimations() {
        const authPage = document.querySelector('.auth-page');
        if (!authPage) {
            return;
        }

        // Animate form fields on focus
        const fields = authPage.querySelectorAll('.field');
        fields.forEach(function (field, index) {
            field.style.animationDelay = (0.1 * (index + 1)) + 's';
        });

        // Smooth transition for error states
        const errorContainers = authPage.querySelectorAll('.auth-errors');
        errorContainers.forEach(function (error) {
            error.style.animation = 'shake 0.5s ease';
        });

        // Add hover effect to role cards
        const roleCards = authPage.querySelectorAll('.auth-role-card');
        roleCards.forEach(function (card) {
            card.addEventListener('mouseenter', function () {
                this.style.transform = 'translateY(-2px)';
            });
            card.addEventListener('mouseleave', function () {
                this.style.transform = 'translateY(0)';
            });
        });

        // Stats cards hover effect
        const statsCards = authPage.querySelectorAll('.auth-side-stats div');
        statsCards.forEach(function (card) {
            card.addEventListener('mouseenter', function () {
                this.style.transform = 'translateY(-4px)';
            });
            card.addEventListener('mouseleave', function () {
                this.style.transform = 'translateY(0)';
            });
        });
    }

    // =========================================
    // Form validation enhancement
    // =========================================
    function setupAuthFormValidation() {
        const authForm = document.querySelector('.auth-form-grid');
        if (!authForm) {
            return;
        }

        // Add real-time validation feedback
        const inputs = authForm.querySelectorAll('input[required]');
        inputs.forEach(function (input) {
            input.addEventListener('blur', function () {
                if (this.value.trim() === '') {
                    this.style.borderColor = '#dc2626';
                } else {
                    this.style.borderColor = '';
                }
            });

            input.addEventListener('input', function () {
                if (this.style.borderColor === 'rgb(220, 38, 38)') {
                    if (this.value.trim() !== '') {
                        this.style.borderColor = '';
                    }
                }
            });
        });

        // Smooth form submission
        authForm.addEventListener('submit', function (e) {
            const submitBtn = this.querySelector('.btn-primary');
            if (submitBtn) {
                submitBtn.style.pointerEvents = 'none';
                submitBtn.style.opacity = '0.7';
                
                // Re-enable after 3 seconds in case of error
                setTimeout(() => {
                    submitBtn.style.pointerEvents = '';
                    submitBtn.style.opacity = '';
                }, 3000);
            }
        });
    }

    // =========================================
    // Smooth scroll to errors
    // =========================================
    function setupErrorScrolling() {
        const authForm = document.querySelector('.auth-form-grid');
        if (!authForm) {
            return;
        }

        const errorContainer = authForm.querySelector('.auth-errors');
        if (errorContainer) {
            errorContainer.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest'
            });
        }
    }

    // =========================================
    // Role card selection enhancement
    // =========================================
    function setupRoleCardSelection() {
        const roleCards = document.querySelectorAll('.auth-role-card');
        roleCards.forEach(function (card) {
            const radio = card.querySelector('input[type="radio"]');
            if (!radio) return;

            // Click entire card to select
            card.addEventListener('click', function (e) {
                if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'BUTTON') {
                    radio.checked = true;
                    // Trigger change event for any listeners
                    radio.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });

            // Keyboard accessibility
            card.setAttribute('tabindex', '0');
            card.setAttribute('role', 'radio');
            if (radio.checked) {
                card.setAttribute('aria-checked', 'true');
            } else {
                card.setAttribute('aria-checked', 'false');
            }

            card.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    radio.checked = true;
                    radio.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });

            radio.addEventListener('change', function () {
                if (radio.checked) {
                    card.setAttribute('aria-checked', 'true');
                    // Add visual feedback
                    card.style.transform = 'scale(1.02)';
                    setTimeout(() => {
                        card.style.transform = '';
                    }, 200);
                } else {
                    card.setAttribute('aria-checked', 'false');
                }
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
    // Header Search & Filters - Compact Version
    // =========================================
    function setupHeaderSearch() {
        const searchContainer = document.querySelector('.header-search');
        const searchToggle = document.querySelector('[data-search-toggle]');
        const searchDropdown = document.querySelector('[data-search-dropdown]');
        const filterToggle = document.querySelector('[data-filter-toggle]');
        const filterDropdown = document.querySelector('[data-filter-dropdown]');
        
        // Handle compact search toggle
        if (searchToggle && searchDropdown) {
            searchToggle.addEventListener('click', function (e) {
                e.preventDefault();
                const isActive = searchDropdown.classList.toggle('active');
                searchToggle.setAttribute('aria-expanded', isActive);
                
                // Close on outside click
                if (isActive) {
                    setTimeout(() => {
                        document.addEventListener('click', closeSearchOutside);
                    }, 0);
                } else {
                    document.removeEventListener('click', closeSearchOutside);
                }
            });

            function closeSearchOutside(e) {
                if (!searchDropdown.contains(e.target) && e.target !== searchToggle) {
                    searchDropdown.classList.remove('active');
                    searchToggle.setAttribute('aria-expanded', 'false');
                    document.removeEventListener('click', closeSearchOutside);
                }
            }
        }

        // Handle filter toggle inside search dropdown
        if (filterToggle && filterDropdown) {
            filterToggle.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                const isActive = filterDropdown.classList.toggle('active');
                filterToggle.setAttribute('aria-expanded', isActive);
            });

            // Save filter state to localStorage
            const inputs = filterDropdown.querySelectorAll('select, input');
            inputs.forEach(function (input) {
                const savedValue = localStorage.getItem('filter_' + input.name);
                if (savedValue && input.value !== savedValue) {
                    input.value = savedValue;
                    updateFilterIndicator();
                }
                
                input.addEventListener('change', function () {
                    localStorage.setItem('filter_' + input.name, input.value);
                    updateFilterIndicator();
                });
            });

            function updateFilterIndicator() {
                const hasActiveFilters = Array.from(inputs).some(input => input.value);
                if (hasActiveFilters) {
                    filterToggle.classList.add('active');
                } else {
                    filterToggle.classList.remove('active');
                }
            }

            // Clear filters on reset button click
            const resetLink = filterDropdown.querySelector('a[href*="event_list"]');
            if (resetLink) {
                resetLink.addEventListener('click', function () {
                    inputs.forEach(function (input) {
                        localStorage.removeItem('filter_' + input.name);
                    });
                    updateFilterIndicator();
                });
            }
        }

        // Close dropdowns on escape key
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                if (searchDropdown) {
                    searchDropdown.classList.remove('active');
                    if (searchToggle) searchToggle.setAttribute('aria-expanded', 'false');
                }
                if (filterDropdown) {
                    filterDropdown.classList.remove('active');
                    if (filterToggle) filterToggle.setAttribute('aria-expanded', 'false');
                }
            }
        });
    }

    // =========================================
    // Initialize
    // =========================================
    document.addEventListener('DOMContentLoaded', function () {
        setupMobileMenu();
        setupPasswordToggles();
        setupAuthAnimations();
        setupAuthFormValidation();
        setupErrorScrolling();
        setupRoleCardSelection();
        setupChatAutoScroll();
        setupNotifications();
        setupFormEnhancements();
        setupHeaderSearch();

        // Expose CSRF helper for inline page scripts
        window.getCookie = getCookie;
    });
})();
