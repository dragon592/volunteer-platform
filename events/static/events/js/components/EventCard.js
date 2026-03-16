/**
 * EventCard - компонент карточки события
 * Переиспользуемый компонент для отображения события в списке
 */
class EventCard {
    constructor(event, options = {}) {
        this.event = event;
        this.options = options;
        this.element = null;
    }
    
    /**
     * Создает DOM элемент карточки
     */
    render() {
        const event = this.event;
        const container = document.createElement('article');
        container.className = 'event-card event-card--modern';
        container.dataset.eventId = event.id;
        
        // Форматируем дату и время
        const dateStr = new Date(event.date).toLocaleDateString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
        const timeStr = event.time ? new Date(`2000-01-01T${event.time}`).toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
        }) : '';
        
        // Вычисляем прогресс
        const registered = event.registered_count || 0;
        const max = event.max_volunteers;
        const progressPercent = (registered / max) * 100;
        const isFull = registered >= max;
        
        container.innerHTML = `
            <div class="event-card__image">
                ${event.image_url ? 
                    `<img src="${event.image_url}" alt="${event.title}" loading="lazy">` :
                    `<div class="event-card__placeholder"><span>Open Hearts</span></div>`
                }
            </div>
            <div class="event-card__content">
                <div class="event-card__badges-top">
                    <span class="badge badge-primary">${event.get_event_type_display || event.event_type}</span>
                    <span class="badge badge-secondary">${event.xp_reward} XP</span>
                </div>
                <h3 class="event-card__title">${event.title}</h3>
                <p class="event-card__description">${event.description ? event.description.substring(0, 150) + '...' : ''}</p>
                
                <div class="event-card__details">
                    <div class="event-card__detail-item">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                            <line x1="16" y1="2" x2="16" y2="6"/>
                            <line x1="8" y1="2" x2="8" y2="6"/>
                            <line x1="3" y1="10" x2="21" y2="10"/>
                        </svg>
                        <span>${dateStr}${timeStr ? ', ' + timeStr : ''}</span>
                    </div>
                    <div class="event-card__detail-item">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/>
                            <circle cx="12" cy="10" r="3"/>
                        </svg>
                        <span>${event.location}${event.city ? ', ' + event.city : ''}</span>
                    </div>
                </div>
                
                <div class="event-card__footer">
                    <div class="event-card__progress">
                        <div class="progress-ring">
                            <svg viewBox="0 0 36 36">
                                <path class="progress-ring__bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                                <path class="progress-ring__circle" stroke-dasharray="${registered}, ${max}" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                            </svg>
                            <div class="progress-ring__text">
                                <span class="progress-count">${registered}</span>
                                <span class="progress-max">/ ${max}</span>
                            </div>
                        </div>
                    </div>
                    <a href="/events/${event.id}/" class="btn btn-primary">
                        ${isFull ? 'Полный' : 'Участвовать'}
                    </a>
                </div>
            </div>
        `;
        
        this.element = container;
        return container;
    }
    
    /**
     * Вставляет карточку в контейнер
     */
    mount(container) {
        if (!this.element) {
            this.render();
        }
        container.appendChild(this.element);
    }
    
    /**
     * Обновляет данные карточки
     */
    update(newEventData) {
        this.event = { ...this.event, ...newEventData };
        if (this.element && this.element.parentNode) {
            this.element.remove();
        }
        this.render();
    }
}

/**
 * Фабрика для создания EventCard
 */
const EventCardFactory = {
    create(event, options = {}) {
        return new EventCard(event, options);
    },
    
    /**
     * Создает и вставляет несколько карточек в контейнер
     */
    createMany(events, container) {
        container.innerHTML = '';
        events.forEach(event => {
            const card = new EventCard(event);
            card.mount(container);
        });
    }
};

// Экспорт
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { EventCard, EventCardFactory };
}
