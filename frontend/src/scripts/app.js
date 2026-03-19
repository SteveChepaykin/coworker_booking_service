document.addEventListener('DOMContentLoaded', () => {
    const API_URL = 'http://localhost:8000/api/v1';
    // In a real app, the user ID would come from an authentication context
    const USER_ID = '22222222-2222-2222-2222-222222222222';

    const spacesList = document.getElementById('spaces-list');
    const roomsList = document.getElementById('rooms-list');
    const roomsHeader = document.getElementById('rooms-header');
    const selectedSpaceName = document.getElementById('selected-space-name');
    const myBookingsList = document.getElementById('my-bookings-list');

    const modal = document.getElementById('booking-modal');
    const modalRoomName = document.getElementById('modal-room-name');
    const modalRoomIdInput = document.getElementById('modal-room-id');
    const closeModalButton = document.querySelector('.close-button');
    const bookingForm = document.getElementById('booking-form');

    // --- Data Fetching Functions ---

    async function fetchSpaces() {
        try {
            const response = await fetch(`${API_URL}/spaces`);
            if (!response.ok) throw new Error('Failed to fetch spaces');
            const spaces = await response.json();
            renderSpaces(spaces);
        } catch (error) {
            console.error('Error fetching spaces:', error);
            spacesList.innerHTML = '<li>Could not load spaces.</li>';
        }
    }

    async function fetchRooms(spaceId, spaceName) {
        try {
            const response = await fetch(`${API_URL}/rooms?coworking_space_id=${spaceId}`);
            if (!response.ok) throw new Error('Failed to fetch rooms');
            const rooms = await response.json();
            renderRooms(rooms, spaceName);
        } catch (error) {
            console.error('Error fetching rooms:', error);
            roomsList.innerHTML = '<li>Could not load rooms.</li>';
        }
    }

    async function fetchMyBookings() {
        try {
            const response = await fetch(`${API_URL}/bookings?user_id=${USER_ID}&future_only=true`);
            if (!response.ok) throw new Error('Failed to fetch bookings');
            const bookings = await response.json();
            renderMyBookings(bookings);
        } catch (error) {
            console.error('Error fetching bookings:', error);
            myBookingsList.innerHTML = '<li>Could not load your bookings.</li>';
        }
    }

    // --- Rendering Functions ---

    function renderSpaces(spaces) {
        spacesList.innerHTML = '';
        if (spaces.length === 0) {
            spacesList.innerHTML = '<li>No spaces found.</li>';
            return;
        }
        spaces.forEach(space => {
            const li = document.createElement('li');
            li.textContent = `${space.name} (${space.city})`;
            li.dataset.spaceId = space.id;
            li.dataset.spaceName = space.name;
            spacesList.appendChild(li);
        });
    }

    function renderRooms(rooms, spaceName) {
        roomsList.innerHTML = '';
        selectedSpaceName.textContent = spaceName;
        roomsHeader.classList.remove('hidden');
        roomsList.classList.remove('hidden');

        if (rooms.length === 0) {
            roomsList.innerHTML = '<li>No rooms available in this space.</li>';
            return;
        }
        rooms.forEach(room => {
            const li = document.createElement('li');
            li.textContent = `${room.name} (Capacity: ${room.capacity})`;
            li.dataset.roomId = room.id;
            li.dataset.roomName = room.name;
            roomsList.appendChild(li);
        });
    }

    function renderMyBookings(bookings) {
        myBookingsList.innerHTML = '';
        if (bookings.length === 0) {
            myBookingsList.innerHTML = '<li>You have no upcoming bookings.</li>';
            return;
        }
        bookings.forEach(booking => {
            const li = document.createElement('li');
            li.classList.add('booking');
            const startTime = new Date(booking.start_time).toLocaleString();
            const endTime = new Date(booking.end_time).toLocaleString();
            li.innerHTML = `<strong>Room ID:</strong> ${booking.room_id.substring(0, 8)}... <br>
                            <strong>From:</strong> ${startTime} <br> 
                            <strong>To:</strong> ${endTime} <br>
                            <strong>Purpose:</strong> ${booking.purpose || 'N/A'}`;
            myBookingsList.appendChild(li);
        });
    }

    // --- Event Handlers ---

    spacesList.addEventListener('click', (e) => {
        if (e.target.tagName === 'LI' && e.target.dataset.spaceId) {
            fetchRooms(e.target.dataset.spaceId, e.target.dataset.spaceName);
        }
    });

    roomsList.addEventListener('click', (e) => {
        if (e.target.tagName === 'LI' && e.target.dataset.roomId) {
            modalRoomName.textContent = e.target.dataset.roomName;
            modalRoomIdInput.value = e.target.dataset.roomId;
            modal.classList.remove('hidden');
        }
    });

    closeModalButton.addEventListener('click', () => modal.classList.add('hidden'));
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.add('hidden');
        }
    });

    bookingForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const bookingData = {
            room_id: modalRoomIdInput.value,
            user_id: USER_ID,
            start_time: new Date(document.getElementById('start-time').value).toISOString(),
            end_time: new Date(document.getElementById('end-time').value).toISOString(),
            purpose: document.getElementById('purpose').value,
        };

        try {
            const response = await fetch(`${API_URL}/bookings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(bookingData),
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create booking');
            }
            alert('Booking created successfully!');
            modal.classList.add('hidden');
            fetchMyBookings(); // Refresh the bookings list
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    });

    // --- Initial Load ---
    fetchSpaces();
    fetchMyBookings();
});