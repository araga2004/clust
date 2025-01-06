class RoomWebSocket {
    constructor(roomId, username, csrfToken, codeEditor) {
        this.roomId = roomId;
        this.username = username;
        this.csrfToken = csrfToken;
        this.socket = null;
        this.messageContainer = document.getElementById('room-message-container');
        this.websocketMessageContainer = document.getElementById('websocket-messages');
        this.messageForm = document.getElementById('message-form');
        this.messageInput = document.getElementById('message-input');
        this.codeEditor = codeEditor;
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const socketUrl = `${protocol}//${window.location.host}/ws/room-code/${this.roomId}/`;

        this.socket = new WebSocket(socketUrl);

        this.socket.onopen = () => {
            console.log('WebSocket connection established');
        };

        this.socket.onmessage = (event) => {
            this.handleIncomingMessage(event);
        };

        this.socket.onclose = () => {
            console.log('WebSocket connection closed');
            // Optional: Attempt to reconnect
            // setTimeout(() => this.connect(), 1000);
        };

        // this.messageForm.addEventListener('submit', (e) => {
        //     e.preventDefault();
        //     this.sendMessage();
        // });
        if (this.codeEditor) {
            this.setupCodeEditorSync();
        }
    }

    sendMessage() {
        const message = this.messageInput.value.trim();

        if (message) {
            this.socket.send(JSON.stringify({
                type: 'chat_message',
                message: message,
                username: this.username
            }));

            this.messageInput.value = '';
        }
    }

    sendCodeChange(codeContent) {
        if (codeContent) {
            this.socket.send(JSON.stringify({
                type: 'code_change',
                code: codeContent,
                username: this.username
            }));
        }
    }

    handleIncomingMessage(event) {
        try {
            const data = JSON.parse(event.data);

            if (data.type === 'chat_message') {
                this.displayMessage(data.username, data.message);
            } else if (data.type === 'code_change') {
                this.updateCodeEditor(data.code);
            }
        } catch (error) {
            console.error('Error parsing message:', error);
        }
    }

    displayMessage(username, message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('thread', 'websocket-message');
        messageElement.innerHTML = `
            <div class="flex gap-3">
                        <div class="flex-1">
                            <div class="flex items-baseline gap-2">
                                <span class="font-medium text-sm">${username}</span>
                                <span class="text-xs text-gray-500">Just Now</span>
                            </div>
                            <p class="text-gray-700 mt-1">${message}</p>
                        </div>
                    </div>`;

        this.websocketMessageContainer.appendChild(messageElement);

        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
    }

    setupCodeEditorSync() {
        this.codeEditor.on("change", (instance, changeObj) => {
            const codeContent = instance.getValue(); // Get the current code content from CodeMirror
            this.sendCodeChange(codeContent);       // Send the updated code
        });
    }

    updateCodeEditor(newCode) {
    if (this.codeEditor && this.codeEditor.getValue() !== newCode) {
        this.codeEditor.setValue(newCode); // Update the CodeMirror content
    }
}
}

document.addEventListener('DOMContentLoaded', () => {
    if (ROOM_ID && USERNAME && CSRF_TOKEN && codeEditor) {
        const roomSocket = new RoomWebSocket(ROOM_ID, USERNAME, CSRF_TOKEN, codeEditor);
        roomSocket.connect();
    } else {
        console.error('Missing required WebSocket initialization parameters');
    }
});
