/**
 * Кастомный хук для работы с событиями
 * Управляет состоянием событий, фильтрацией, загрузкой
 */
class EventStore {
    constructor() {
        this.events = [];
        this.loading = false;
        this.error = null;
        this.filters = {
            tab: 'current',
            skill: '',
            city: '',
            search: '',
            event_type: '',
            status: '',
            date_from: '',
            date_to: '',
            participant: '',
            sort: 'date_asc',
        };
        this.listeners = [];
    }
    
    /**
     * Подписка на изменения состояния
     */
    subscribe(listener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }
    
    /**
     * Уведомляет всех подписчиков об изменении состояния
     */
    notify() {
        this.listeners.forEach(listener => listener(this.getState()));
    }
    
    /**
     * Возвращает текущее состояние
     */
    getState() {
        return {
            events: this.events,
            loading: this.loading,
            error: this.error,
            filters: { ...this.filters },
        };
    }
    
    /**
     * Устанавливает фильтры
     */
    setFilters(newFilters) {
        this.filters = { ...this.filters, ...newFilters };
        this.notify();
    }
    
    /**
     * Загружает события с сервера
     */
    async loadEvents() {
        this.loading = true;
        this.error = null;
        this.notify();
        
        try {
            const params = { ...this.filters };
            // Удаляем пустые параметры
            Object.keys(params).forEach(key => {
                if (!params[key]) delete params[key];
            });
            
            const response = await EventAPI.getEvents(params);
            
            if (response && response.events) {
                this.events = response.events;
                // Сохраняем метаданные пагинации если есть
                if (response.page_obj) {
                    this.pagination = {
                        page: response.page_obj.number,
                        num_pages: response.page_obj.paginator.num_pages,
                        total: response.page_obj.paginator.count,
                    };
                }
            } else {
                this.events = [];
            }
            
            this.loading = false;
            this.notify();
        } catch (error) {
            console.error('Failed to load events:', error);
            this.error = error.message || 'Ошибка загрузки событий';
            this.loading = false;
            this.events = [];
            this.notify();
        }
    }
    
    /**
     * Сбрасывает состояние
     */
    reset() {
        this.events = [];
        this.loading = false;
        this.error = null;
        this.notify();
    }
}

/**
 * Создает и возвращает экземпляр EventStore
 */
let eventStoreInstance = null;

function getEventStore() {
    if (!eventStoreInstance) {
        eventStoreInstance = new EventStore();
    }
    return eventStoreInstance;
}

/**
 * Хук для использования в React или других фреймворках
 * Возвращает состояние и методы для работы с событиями
 */
function useEvents() {
    const store = getEventStore();
    const [state, setState] = useState ? useState(store.getState()) : null;
    
    // Подписываемся на изменения
    useEffect(() => {
        if (!state) return;
        
        const unsubscribe = store.subscribe((newState) => {
            if (state) {
                setState(newState);
            }
        });
        
        return unsubscribe;
    }, [state]);
    
    return {
        ...store.getState(),
        setFilters: (filters) => store.setFilters(filters),
        loadEvents: () => store.loadEvents(),
        reset: () => store.reset(),
    };
}

/**
 * Инициализация хука при загрузке страницы
 * Автоматически загружает события если элемент существует
 */
function initEventHook(containerSelector = '.events-grid') {
    const store = getEventStore();
    const container = document.querySelector(containerSelector);
    
    if (!container) return;
    
    // Загружаем события при инициализации
    store.loadEvents();
    
    // Подписываемся на изменения и обновляем DOM
    const unsubscribe = store.subscribe((state) => {
        if (state.events.length > 0) {
            EventCardFactory.createMany(state.events, container);
        } else if (state.loading) {
            container.innerHTML = '<div class="loading">Загрузка...</div>';
        } else if (state.error) {
            container.innerHTML = `<div class="error">${state.error}</div>`;
        } else {
            container.innerHTML = '<div class="empty">События не найдены</div>';
        }
    });
    
    return unsubscribe;
}

// Экспорт
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        EventStore,
        getEventStore,
        useEvents,
        initEventHook,
    };
}
