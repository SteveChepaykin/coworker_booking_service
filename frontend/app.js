document.addEventListener('DOMContentLoaded', () => {
    // --- CONFIGURATION ---
    const API_BASE_URL = '/api/v1';
    const CURRENT_USER_ID = '22222222-2222-2222-2222-222222222222'; // Hardcoded for now

    // --- DOM ELEMENT REFERENCES ---
    const ui = {
        spaces: { 
            list: document.getElementById('spaces-list'),
            loader: document.getElementById('spaces-loader'),
            error: document.getElementById('spaces-error'),
        },
        bookings: {
            list: document.getElementById('my-bookings-list'),
            empty: document.getElementById('bookings-empty'),
            loader: document.getElementById('bookings-loader'),
            error: document.getElementById('bookings-error'),
        },
        modal: {
            element: document.getElementById('booking-modal'),
            closeButton: document.getElementById('modal-close'),
            overlay: document.querySelector('.modal-overlay'),
            step1: document.getElementById('step-1-rooms'),
            step2: document.getElementById('step-2-datetime'),
            step3: document.getElementById('step-3-success'),
            roomsList: document.getElementById('rooms-list'),
            spaceName: document.getElementById('modal-space-name'),
            roomName: document.getElementById('modal-room-name'),
            backBtn: document.getElementById('back-to-rooms'),
            dateInput: document.getElementById('booking-date'),
            form: document.getElementById('booking-form'),
            error: document.getElementById('modal-error'),
            finishBtn: document.getElementById('finish-booking-btn'),
            submitBtn: document.getElementById('confirm-booking-btn'),
            timeline: {
                track: document.getElementById('timeline-track'),
                selected: document.getElementById('timeline-selected'),
                hStart: document.getElementById('handle-start'),
                hEnd: document.getElementById('handle-end'),
                tStart: document.getElementById('tooltip-start'),
                tEnd: document.getElementById('tooltip-end'),
                blocks: document.getElementById('timeline-blocks'),
                inStart: document.getElementById('startTime'),
                inEnd: document.getElementById('endTime'),
            }
        },
        detailsModal: {
            element: document.getElementById('booking-details-modal'),
            closeBtn: document.getElementById('details-close'),
            overlay: document.querySelector('#booking-details-modal .modal-overlay'),
            image: document.getElementById('details-image'),
            roomName: document.getElementById('details-room-name'),
            time: document.getElementById('details-time'),
            purpose: document.getElementById('details-purpose'),
            deleteBtn: document.getElementById('delete-booking-btn'),
        },
        templates: {
            bookingItem: document.getElementById('booking-item-template'),
        }
    };

    const MIN_HOUR = 9; const MAX_HOUR = 18; const STEP = 0.5;

    // --- STATE MANAGEMENT ---
    const state = {
        spaces: [],
        rooms: [],
        bookings: [],
        roomDetailsCache: {},
        activeRoom: null,
        activeBooking: null,
        bookedRanges: [], // Times booked for selected date
        timeStart: 9,
        timeEnd: 10,
        activeDragHandle: null
    };

    // --- UTILITY FUNCTIONS ---
    const show = (el) => el.classList.remove('hidden');
    const hide = (el) => el.classList.add('hidden');

    // --- API SERVICE ---
    const api = {
        async fetch(url, options = {}) {
            try {
                const response = await fetch(url, options);
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
                    throw new Error(errorData.detail || `Request failed with status ${response.status}`);
                }
                if (response.status === 204) return null;
                return response.json();
            } catch (error) {
                console.error(`API call to ${url} failed:`, error);
                throw error; // Re-throw to be handled by the caller
            }
        },
        getSpaces: () => api.fetch(`${API_BASE_URL}/spaces/`),
        getRooms: (spaceId) => api.fetch(`${API_BASE_URL}/rooms/?coworking_space_id=${spaceId}`),
        getRoomDetails: (roomId) => api.fetch(`${API_BASE_URL}/rooms/${roomId}`),
        getAllBookings: () => api.fetch(`${API_BASE_URL}/bookings/`), // For timeline collision
        getBookings: () => api.fetch(`${API_BASE_URL}/bookings/?user_id=${CURRENT_USER_ID}&future_only=true`),
        createBooking: (bookingData) => api.fetch(`${API_BASE_URL}/bookings/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(bookingData),
        }),
        deleteBooking: (id) => api.fetch(`${API_BASE_URL}/bookings/${id}`, { method: 'DELETE' }),
    };

    // --- RENDER FUNCTIONS ---
    const render = {
        spaces() {
            ui.spaces.list.innerHTML = '';
            state.spaces.forEach(space => {
                const div = document.createElement('div');
                div.className = 'card space-card';
                div.dataset.id = space.id;
                div.dataset.name = space.name;
                div.innerHTML = `
                    <img src="${space.image_link || ''}" class="card-img">
                    <div class="card-content">
                        <h3 class="item-name">${space.name}</h3>
                        <p class="text-muted">${space.address}, ${space.city}</p>
                    </div>`;
                ui.spaces.list.appendChild(div);
            });
        },
        rooms() {
            ui.modal.roomsList.innerHTML = '';
            state.rooms.forEach(room => {
                if (!room.is_active) return;
                const div = document.createElement('div');
                div.className = 'card room-card';
                div.dataset.id = room.id;
                div.dataset.name = room.name;
                div.innerHTML = `
                    <img src="${room.image_link || ''}" class="card-img">
                    <div class="card-content">
                        <h3 class="item-name">${room.name}</h3>
                        <p class="text-muted">👥 Capacity: ${room.capacity}</p>
                    </div>`;
                ui.modal.roomsList.appendChild(div);
            });
        },
        async bookings() {
            ui.bookings.list.innerHTML = '';
            if (state.bookings.length === 0) {
                show(ui.bookings.empty);
                return;
            }
            hide(ui.bookings.empty)

            const roomPromises = state.bookings.map(booking => {
                if (state.roomDetailsCache[booking.room_id]) return state.roomDetailsCache[booking.room_id];
                return api.getRoomDetails(booking.room_id).then(room => {
                    state.roomDetailsCache[booking.room_id] = room;
                    return room;
                });
            });

            const rooms = await Promise.all(roomPromises);
            state.bookings.forEach((booking, index) => {
                const room = rooms[index];
                const template = ui.templates.bookingItem.content.cloneNode(true);

                const div = template.querySelector('.card');
                div.dataset.id = booking.id;
                const dStart = new Date(booking.start_time);
                const dEnd = new Date(booking.end_time);
                
                template.querySelector('.booking-room-name').textContent = room ? room.name : "Room";
                template.querySelector('.booking-time').textContent = 
                    `${dStart.toLocaleDateString()} | ${dStart.getHours()}:${String(dStart.getMinutes()).padStart(2, '0')} - ${dEnd.getHours()}:${String(dEnd.getMinutes()).padStart(2, '0')}`;
                ui.bookings.list.appendChild(template);
            });
        },
    };

    // --- TIMELINE LOGIC ---
    const timeline = {
        formatTime(dec) {
            const h = Math.floor(dec);
            const m = dec % 1 === 0 ? '00' : '30';
            return `${String(h).padStart(2,'0')}:${m}`;
        },
        updateUI() {
            const pStart = ((state.timeStart - MIN_HOUR) / (MAX_HOUR - MIN_HOUR)) * 100;
            const pEnd = ((state.timeEnd - MIN_HOUR) / (MAX_HOUR - MIN_HOUR)) * 100;
            
            ui.modal.timeline.hStart.style.left = `${pStart}%`;
            ui.modal.timeline.hEnd.style.left = `${pEnd}%`;
            ui.modal.timeline.selected.style.left = `${pStart}%`;
            ui.modal.timeline.selected.style.width = `${pEnd - pStart}%`;
            
            ui.modal.timeline.tStart.textContent = timeline.formatTime(state.timeStart);
            ui.modal.timeline.tEnd.textContent = timeline.formatTime(state.timeEnd);
            
            const colliding = timeline.isColliding(state.timeStart, state.timeEnd);
            if (colliding) {
                ui.modal.timeline.selected.classList.add('invalid');
                ui.modal.submitBtn.disabled = true;
            } else {
                ui.modal.timeline.selected.classList.remove('invalid');
                ui.modal.submitBtn.disabled = false;
            }
        },
        isColliding(start, end) {
            return state.bookedRanges.some(b => Math.max(start, b.start) < Math.min(end, b.end));
        },
        handleDrag(e) {
            if (!state.activeDragHandle) return;
            const rect = ui.modal.timeline.track.getBoundingClientRect();
            let x = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
            let percent = x / rect.width;
            let time = MIN_HOUR + percent * (MAX_HOUR - MIN_HOUR);
            time = Math.round(time / STEP) * STEP;

            if (state.activeDragHandle === 'start') {
                if (time >= state.timeEnd) time = state.timeEnd - STEP;
                state.timeStart = time;
            } else {
                if (time <= state.timeStart) time = state.timeStart + STEP;
                state.timeEnd = time;
            }
            timeline.updateUI();
        },
        async loadBookedBlocks(dateStr) {
            ui.modal.timeline.blocks.innerHTML = '';
            const allBookings = await api.getAllBookings(); // Naive fetch for demo timeline
            state.bookedRanges = allBookings
                .filter(b => b.room_id === state.activeRoom && b.status === 'confirmed' && b.start_time.startsWith(dateStr))
                .map(b => {
                    const ds = new Date(b.start_time);
                    const de = new Date(b.end_time);
                    return { start: ds.getHours() + (ds.getMinutes() / 60), end: de.getHours() + (de.getMinutes() / 60) };
                });
            
            state.bookedRanges.forEach(b => {
                const block = document.createElement('div');
                block.className = 'timeline-booked-block';
                block.style.left = `${((Math.max(b.start, MIN_HOUR) - MIN_HOUR) / (MAX_HOUR - MIN_HOUR)) * 100}%`;
                block.style.width = `${((Math.min(b.end, MAX_HOUR) - Math.max(b.start, MIN_HOUR)) / (MAX_HOUR - MIN_HOUR)) * 100}%`;
                ui.modal.timeline.blocks.appendChild(block);
            });
            
            state.timeStart = 9; state.timeEnd = 10;
            timeline.updateUI();
        }
    };

    // --- EVENT HANDLERS ---
    const handlers = {
        async handleSpaceClick(event) {
            const target = event.target.closest('.space-card');
            if (!target) return;
            ui.modal.spaceName.textContent = target.dataset.name;
            state.rooms = await api.getRooms(target.dataset.id);
            render.rooms();
            
            hide(ui.modal.step2); hide(ui.modal.step3); show(ui.modal.step1);
            show(ui.modal.element);
        },

        handleRoomClick(event) {
            const target = event.target.closest('.room-card');
            if (!target) return;
            state.activeRoom = target.dataset.id;
            ui.modal.roomName.textContent = target.dataset.name;
            
            const today = new Date().toISOString().split('T')[0];
            ui.modal.dateInput.value = today;
            timeline.loadBookedBlocks(today);
            
            hide(ui.modal.step1); show(ui.modal.step2);
        },

        closeModal() {
            hide(ui.modal.element);
            load.bookings();
        },

        handleBookingClick(event) {
            const target = event.target.closest('.booking-card');
            if (!target) return;
            
            const booking = state.bookings.find(b => b.id === target.dataset.id);
            if (!booking) return;

            const room = state.roomDetailsCache[booking.room_id];
            state.activeBooking = booking.id;

            ui.detailsModal.roomName.textContent = room ? room.name : "Room";
            ui.detailsModal.image.src = room?.image_link || '';
            
            const dStart = new Date(booking.start_time);
            const dEnd = new Date(booking.end_time);
            ui.detailsModal.time.textContent = `${dStart.toLocaleDateString()} | ${dStart.getHours()}:${String(dStart.getMinutes()).padStart(2, '0')} - ${dEnd.getHours()}:${String(dEnd.getMinutes()).padStart(2, '0')}`;
            
            ui.detailsModal.purpose.textContent = booking.purpose || 'No purpose specified.';
            
            show(ui.detailsModal.element);
        },
        
        closeDetailsModal() {
            hide(ui.detailsModal.element);
        },

        async handleDeleteBooking() {
            if (!state.activeBooking) return;
            const confirmDelete = confirm("Are you sure you want to cancel this booking?");
            if (!confirmDelete) return;
            
            const originalText = ui.detailsModal.deleteBtn.textContent;
            ui.detailsModal.deleteBtn.textContent = 'Canceling...';
            ui.detailsModal.deleteBtn.disabled = true;

            try {
                await api.deleteBooking(state.activeBooking);
                hide(ui.detailsModal.element);
                await load.bookings();
            } catch (error) {
                alert(`Failed to cancel booking: ${error.message}`);
            } finally {
                ui.detailsModal.deleteBtn.textContent = originalText;
                ui.detailsModal.deleteBtn.disabled = false;
            }
        },

        async handleBookingSubmit(event) {
            event.preventDefault();
            hide(ui.modal.error);

            const dateBase = ui.modal.dateInput.value;
            const dStart = new Date(`${dateBase}T${timeline.formatTime(state.timeStart)}:00Z`);
            const dEnd = new Date(`${dateBase}T${timeline.formatTime(state.timeEnd)}:00Z`);

            const bookingData = {
                room_id: state.activeRoom,
                user_id: CURRENT_USER_ID,
                start_time: dStart.toISOString(),
                end_time: dEnd.toISOString(),
                purpose: document.getElementById('purpose').value,
            };

            try {
                await api.createBooking(bookingData);
                hide(ui.modal.step2); show(ui.modal.step3);
            } catch (error) {
                ui.modal.error.textContent = `Error: ${error.message}`;
                show(ui.modal.error);
            }
        },
    };

    // --- DATA LOADING ---
    const load = {
        async spaces() {
            show(ui.spaces.loader);
            hide(ui.spaces.error);
            try {
                state.spaces = await api.getSpaces();
                render.spaces();
            } catch (error) {
                ui.spaces.error.textContent = `Could not load spaces: ${error.message}`;
                show(ui.spaces.error);
            } finally {
                hide(ui.spaces.loader);
            }
        },
        async bookings() {
            show(ui.bookings.loader);
            hide(ui.bookings.error);
            try {
                state.bookings = await api.getBookings();
                await render.bookings();
            } catch (error) {
                ui.bookings.error.textContent = `Could not load bookings: ${error.message}`;
                show(ui.bookings.error);
            } finally {
                hide(ui.bookings.loader);
            }
        },
    };

    // --- INITIALIZATION ---
    function initialize() {
        ui.spaces.list.addEventListener('click', handlers.handleSpaceClick);
        ui.modal.roomsList.addEventListener('click', handlers.handleRoomClick);
        ui.modal.closeButton.addEventListener('click', handlers.closeModal);
        ui.modal.overlay.addEventListener('click', handlers.closeModal);
        ui.modal.finishBtn.addEventListener('click', handlers.closeModal);
        ui.modal.backBtn.addEventListener('click', () => { hide(ui.modal.step2); show(ui.modal.step1); });
        ui.modal.form.addEventListener('submit', handlers.handleBookingSubmit);
        
        ui.bookings.list.addEventListener('click', handlers.handleBookingClick);
        ui.detailsModal.closeBtn.addEventListener('click', handlers.closeDetailsModal);
        ui.detailsModal.overlay.addEventListener('click', handlers.closeDetailsModal);
        ui.detailsModal.deleteBtn.addEventListener('click', handlers.handleDeleteBooking);

        ui.modal.dateInput.addEventListener('change', (e) => timeline.loadBookedBlocks(e.target.value));
        
        ui.modal.timeline.hStart.addEventListener('mousedown', () => state.activeDragHandle = 'start');
        ui.modal.timeline.hEnd.addEventListener('mousedown', () => state.activeDragHandle = 'end');
        window.addEventListener('mouseup', () => state.activeDragHandle = null);
        window.addEventListener('mousemove', timeline.handleDrag);

        window.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                if (!ui.modal.element.classList.contains('hidden')) handlers.closeModal();
                if (!ui.detailsModal.element.classList.contains('hidden')) handlers.closeDetailsModal();
            }
        });

        // Initial Data Load
        load.spaces();
        load.bookings();
    }

    initialize();
});