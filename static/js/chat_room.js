const roomName = JSON.parse(document.getElementById('room-name').textContent);

const chatSocket = new WebSocket(
    (window.location.protocol === 'https:' ? 'wss://' : 'ws://') +
    window.location.host +
    '/ws/chat/' + roomName + '/'
);

chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    const chatLog = document.querySelector('#chat-log');

    if (data.action === 'new') {
        // Add the user name and message
        chatLog.value += `${data.user}: ${data.message}\n`;
    } else if (data.action === 'edit') {
        // Update existing message based on ID
        const messageRegex = new RegExp(`^.*${data.id}.*$`, 'm');
        chatLog.value = chatLog.value.replace(messageRegex, `${data.user}: ${data.message}`);
    } else if (data.action === 'delete') {
        // Remove message based on ID
        const messageRegex = new RegExp(`^.*${data.id}.*$`, 'm');
        chatLog.value = chatLog.value.replace(messageRegex, '');
    }
};

document.querySelector('#chat-message-input').onkeyup = function(e) {
    if (e.key === 'Enter') {
        document.querySelector('#chat-message-submit').click();
    }
};

document.querySelector('#chat-message-submit').onclick = function(e) {
    const messageInputDom = document.querySelector('#chat-message-input');
    const message = messageInputDom.value.trim();
    if (message) {
        chatSocket.send(JSON.stringify({
            'action': 'send',
            'message': message
        }));
        messageInputDom.value = '';
    }
};

document.querySelector('#edit-message-submit').onclick = function(e) {
    const messageId = document.querySelector('#edit-message-id').value;
    const newContent = document.querySelector('#edit-message-input').value.trim();
    if (messageId && newContent) {
        chatSocket.send(JSON.stringify({
            'action': 'edit',
            'id': messageId,
            'message': newContent
        }));
        document.querySelector('#edit-message-input').value = '';
        document.querySelector('#edit-message-id').value = '';
    }
};

document.querySelector('#delete-message-submit').onclick = function(e) {
    const messageId = document.querySelector('#delete-message-id').value;
    if (messageId) {
        chatSocket.send(JSON.stringify({
            'action': 'delete',
            'id': messageId
        }));
        document.querySelector('#delete-message-id').value = '';
    }
};

// Example of how to set edit mode (for demonstration purposes)
function enterEditMode(messageId, currentContent) {
    document.querySelector('#edit-message-id').value = messageId;
    document.querySelector('#edit-message-input').value = currentContent;
}
