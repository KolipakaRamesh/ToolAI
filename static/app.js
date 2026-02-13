const messagesContainer = document.getElementById('messages');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');

// Tool icons mapping
const toolIcons = {
    'calculator': '🧮',
    'get_weather': '🌤️',
    'analyze_data': '📊',
    'generate_password': '🔐',
    'validate_email': '📧',
    'convert_currency': '💱'
};

// Add message to chat
function addMessage(text, isUser = false, toolUsed = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'assistant-message'}`;

    const avatar = isUser ? '👤' : '🤖';

    let toolBadge = '';
    if (toolUsed) {
        const toolIcon = toolIcons[toolUsed.name] || '🔧';
        const toolNames = {
            'calculator': 'Calculator',
            'get_weather': 'Weather',
            'analyze_data': 'Data Analyzer',
            'generate_password': 'Password Generator',
            'validate_email': 'Email Address Validator',
            'convert_currency': 'Currency Converter'
        };
        const toolDisplayName = toolNames[toolUsed.name] || toolUsed.name;

        toolBadge = `
            <div class="tool-badge">
                <span class="tool-icon">${toolIcon}</span>
                <span>Used ${toolDisplayName}</span>
            </div>
        `;
    }

    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="avatar">${avatar}</div>
            <div class="text">
                <p>${escapeHtml(text)}</p>
                ${toolBadge}
            </div>
        </div>
    `;

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Add loading indicator
function addLoading() {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant-message';
    loadingDiv.id = 'loading-message';

    loadingDiv.innerHTML = `
        <div class="message-content">
            <div class="avatar">🤖</div>
            <div class="text">
                <div class="loading">
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                </div>
            </div>
        </div>
    `;

    messagesContainer.appendChild(loadingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Remove loading indicator
function removeLoading() {
    const loadingMessage = document.getElementById('loading-message');
    if (loadingMessage) {
        loadingMessage.remove();
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Handle form submission
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const message = userInput.value.trim();
    if (!message) return;

    // Add user message
    addMessage(message, true);

    // Clear input
    userInput.value = '';

    // Disable input while processing
    userInput.disabled = true;
    sendButton.disabled = true;

    // Show loading
    addLoading();

    try {
        // Send request to backend
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });

        if (!response.ok) {
            throw new Error('Failed to get response');
        }

        const data = await response.json();

        // Remove loading
        removeLoading();

        // Add assistant response
        addMessage(data.response, false, data.tool_used);

    } catch (error) {
        console.error('Error:', error);
        removeLoading();
        addMessage('Sorry, I encountered an error. Please try again.', false);
    } finally {
        // Re-enable input
        userInput.disabled = false;
        sendButton.disabled = false;
        userInput.focus();
    }
});

// Focus input on load
userInput.focus();
