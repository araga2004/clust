class RoomWebSocket {
    constructor(roomId, username, csrfToken) {
        this.roomId = roomId;
        this.username = username;
        this.csrfToken = csrfToken;
        this.socket = null;
        this.messageContainer = document.getElementById('room-message-container');
        this.websocketMessageContainer = document.getElementById('websocket-messages');
        this.messageForm = document.getElementById('message-form');
        this.messageInput = document.getElementById('message-input');
    }

    connect() {
        // Determine the WebSocket URL based on current protocol
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const socketUrl = `${protocol}//${window.location.host}/ws/room/${this.roomId}/`;

        this.socket = new WebSocket(socketUrl);

        this.socket.onopen = () => {
            console.log('WebSocket connection established');
        };

        this.socket.onmessage = (event) => {
            this.handleIncomingMessage(event);
            console.log('message done')
        };

        this.socket.onclose = () => {
            console.log('WebSocket connection closed');
            // Optional: Attempt to reconnect
            //setTimeout(() => this.connect(), 1000);
        };

        // Attach form submit event
        this.messageForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
            console.log('message gone')
        });
    }

    sendMessage() {
        const message = this.messageInput.value.trim();
        
        if (message) {
            // Send message via WebSocket
            this.socket.send(JSON.stringify({
                'message': message,
                'username': this.username
            }));

            // Clear input
            this.messageInput.value = '';
        }
    }

    handleIncomingMessage(event) {
        try {
            const data = JSON.parse(event.data);
            this.displayMessage(data.username, data.message);
        } catch (error) {
            console.error('Error parsing message:', error);
        }
    }

    displayMessage(username, message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('thread', 'websocket-message');
        messageElement.innerHTML = `
            <div class="thread__top">
                <div class="thread__author">
                    <a href="/profile/${username}" class="thread__authorInfo">
                        <div class="avatar avatar--small">
                            <img src="https://randomuser.me/api/portraits/men/37.jpg" />
                        </div>
                        <span>@${username}</span>
                    </a>
                    <span class="thread__date">Just now</span>
                </div>
            </div>
            <div class="thread__details">
                ${message}
            </div>
        `;

        this.websocketMessageContainer.appendChild(messageElement);
        
        // Auto-scroll to bottom
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
    }
}

// Initialize WebSocket on page load
document.addEventListener('DOMContentLoaded', () => {
    if (ROOM_ID && USERNAME && CSRF_TOKEN) {
        const roomSocket = new RoomWebSocket(ROOM_ID, USERNAME, CSRF_TOKEN);
        roomSocket.connect();
    } else {
        console.error('Missing required WebSocket initialization parameters');
    }
});