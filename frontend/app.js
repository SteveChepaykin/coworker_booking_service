document.addEventListener('DOMContentLoaded', () => {
    // --- CONFIGURATION ---
    const API_BASE_URL = '/api/v1';
    const CURRENT_USER_ID = '22222222-2222-2222-2222-222222222222'; // Hardcoded for now

    // --- DOM ELEMENT REFERENCES ---
    const ui = {
        spaces: {
            section: document.getElementById('spaces-section'),
            list: document.getElementById('spaces-list'),
            loader: document.getElementById('spaces-loader'),
            error: document.getElementById('spaces-error'),
        },
        rooms: {
            section: document.getElementById('rooms-section'),
            list: document.getElementById('rooms-list'),
            loader: document.getElementById('rooms-loader'),
            error: document.getElementById('rooms-error'),
            headerName: document.getElementById('selected-space-name'),
        },
        bookings: {
            list: document.getElementById('my-bookings-list'),
            loader: document.getElementById('bookings-loader'),
            error: document.getElementById('bookings-error'),
        },
        modal: {
            element: document.getElementById('booking-modal'),
            content: document.querySelector('.modal-content'),
            closeButton: document.querySelector('.close-button'),
            overlay: document.querySelector('.modal-overlay'),
            roomName: document.getElementById('modal-room-name'),
            roomIdInput: document.getElementById('modal-room-id'),
            form: document.getElementById('booking-form'),
            loader: document.getElementById('modal-loader'),
            error: document.getElementById('modal-error'),
            submitButton: document.getElementById('confirm-booking-btn'),
        },
        templates: {
            spaceItem: document.getElementById('space-item-template'),
            roomItem: document.getElementById('room-item-template'),
            bookingItem: document.getElementById('booking-item-template'),
        }
    };

    // --- STATE MANAGEMENT ---
    const state = {
        spaces: [],
        rooms: [],
        bookings: [],
        selectedSpaceId: null,
        roomDetailsCache: {}, // Cache for room details to reduce API calls
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
                return response.json();
            } catch (error) {
                console.error(`API call to ${url} failed:`, error);
                throw error; // Re-throw to be handled by the caller
            }
        },
        getSpaces: () => api.fetch(`${API_BASE_URL}/spaces/`),
        getRooms: (spaceId) => api.fetch(`${API_BASE_URL}/rooms/?coworking_space_id=${spaceId}`),
        getRoomDetails: (roomId) => api.fetch(`${API_BASE_URL}/rooms/${roomId}`),
        getBookings: () => api.fetch(`${API_BASE_URL}/bookings/?user_id=${CURRENT_USER_ID}&future_only=true`),
        createBooking: (bookingData) => api.fetch(`${API_BASE_URL}/bookings/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(bookingData),
        }),
    };

    // --- RENDER FUNCTIONS ---
    const render = {
        spaces() {
            ui.spaces.list.innerHTML = '';
            if (state.spaces.length === 0) {
                ui.spaces.list.innerHTML = '<li>No coworking spaces found.</li>';
                return;
            }
            state.spaces.forEach(space => {
                const template = ui.templates.spaceItem.content.cloneNode(true);
                const li = template.querySelector('li');
                li.dataset.spaceId = space.id;
                li.dataset.spaceName = space.name;
                li.querySelector('.item-name').textContent = space.name;
                li.querySelector('.item-detail').textContent = `${space.address}, ${space.city}`;
                if (space.id === state.selectedSpaceId) {
                    li.classList.add('selected');
                }
                ui.spaces.list.appendChild(template);
            });
        },
        rooms() {
            ui.rooms.list.innerHTML = '';
            if (state.rooms.length === 0) {
                ui.rooms.list.innerHTML = '<li>No rooms available in this space.</li>';
                return;
            }
            state.rooms.forEach(room => {
                if (!room.is_active) return;
                const template = ui.templates.roomItem.content.cloneNode(true);
                const li = template.querySelector('li');
                li.dataset.roomId = room.id;
                li.dataset.roomName = room.name;
                li.querySelector('.item-name').textContent = room.name;
                li.querySelector('.item-detail').textContent = `Capacity: ${room.capacity}`;
                ui.rooms.list.appendChild(template);
            });
        },
        async bookings() {
            ui.bookings.list.innerHTML = '';
            if (state.bookings.length === 0) {
                ui.bookings.list.innerHTML = '<li>You have no upcoming bookings.</li>';
                return;
            }

            // NOTE: This approach causes an N+1 query problem. For a production app with many
            // bookings, the backend should provide an endpoint that returns bookings with
            // pre-joined room details to solve this.
            const roomPromises = state.bookings.map(booking => {
                if (state.roomDetailsCache[booking.room_id]) {
                    return Promise.resolve(state.roomDetailsCache[booking.room_id]);
                }
                return api.getRoomDetails(booking.room_id).then(room => {
                    state.roomDetailsCache[booking.room_id] = room; // Cache the result
                    return room;
                });
            });

            const rooms = await Promise.all(roomPromises);

            state.bookings.forEach((booking, index) => {
                const room = rooms[index];
                const template = ui.templates.bookingItem.content.cloneNode(true);
                const li = template.querySelector('li');
                const startTime = new Date(booking.start_time).toLocaleString();
                const endTime = new Date(booking.end_time).toLocaleString();

                li.innerHTML = `
                    <strong>Room:</strong> ${room ? room.name : `ID ${booking.room_id.substring(0, 8)}...`}<br>
                    <strong>From:</strong> ${startTime} <br> 
                    <strong>To:</strong> ${endTime} <br>
                    <strong>Purpose:</strong> ${booking.purpose || 'N/A'}
                `;
                ui.bookings.list.appendChild(template);
            });
        },
    };

    // --- EVENT HANDLERS ---
    const handlers = {
        async handleSpaceClick(event) {
            const target = event.target.closest('li.item');
            if (!target || !target.dataset.spaceId) return;

            const { spaceId, spaceName } = target.dataset;
            state.selectedSpaceId = spaceId;
            render.spaces(); // Re-render to show selection

            show(ui.rooms.section);
            show(ui.rooms.loader);
            hide(ui.rooms.error);
            ui.rooms.list.innerHTML = '';
            ui.rooms.headerName.textContent = spaceName;

            try {
                state.rooms = await api.getRooms(spaceId);
                render.rooms();
            } catch (error) {
                ui.rooms.error.textContent = `Could not load rooms: ${error.message}`;
                show(ui.rooms.error);
            } finally {
                hide(ui.rooms.loader);
            }
        },

        handleRoomClick(event) {
            const target = event.target.closest('li.bookable');
            if (!target || !target.dataset.roomId) return;

            ui.modal.roomName.textContent = target.dataset.roomName;
            ui.modal.roomIdInput.value = target.dataset.roomId;
            ui.modal.form.reset();
            hide(ui.modal.error);
            show(ui.modal.element);
        },

        closeModal() {
            hide(ui.modal.element);
        },

        async handleBookingSubmit(event) {
            event.preventDefault();
            ui.modal.submitButton.disabled = true;
            ui.modal.submitButton.textContent = 'Booking...';
            hide(ui.modal.error);

            const formData = new FormData(ui.modal.form);
            const startTime = new Date(formData.get('startTime'));
            const endTime = new Date(formData.get('endTime'));

            if (isNaN(startTime) || isNaN(endTime) || startTime >= endTime) {
                ui.modal.error.textContent = 'Please select a valid start and end time.';
                show(ui.modal.error);
                ui.modal.submitButton.disabled = false;
                ui.modal.submitButton.textContent = 'Confirm Booking';
                return;
            }

            const bookingData = {
                room_id: formData.get('roomId'),
                user_id: CURRENT_USER_ID,
                start_time: startTime.toISOString(),
                end_time: endTime.toISOString(),
                purpose: formData.get('purpose'),
            };

            try {
                await api.createBooking(bookingData);
                handlers.closeModal();
                await load.bookings(); // Refresh bookings list
            } catch (error) {
                ui.modal.error.textContent = `Error: ${error.message}`;
                show(ui.modal.error);
            } finally {
                ui.modal.submitButton.disabled = false;
                ui.modal.submitButton.textContent = 'Confirm Booking';
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
        // Setup Event Listeners
        ui.spaces.list.addEventListener('click', handlers.handleSpaceClick);
        ui.rooms.list.addEventListener('click', handlers.handleRoomClick);
        ui.modal.closeButton.addEventListener('click', handlers.closeModal);
        ui.modal.overlay.addEventListener('click', handlers.closeModal);
        ui.modal.form.addEventListener('submit', handlers.handleBookingSubmit);

        // Close modal with Escape key
        window.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && !ui.modal.element.classList.contains('hidden')) {
                handlers.closeModal();
            }
        });

        // Initial Data Load
        load.spaces();
        load.bookings();
    }

    initialize();
});