const API_BASE_URL = "http://127.0.0.1:8000";

/**
 * RGCET Help Desk Widget Logic
 * This script handles the UI interactions for the chatbot widget shell.
 */
document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const launcher = document.getElementById('rgcet-launcher');
    const panel = document.getElementById('rgcet-panel');
    const closeBtn = document.getElementById('rgcet-close-btn');
    const messagesArea = document.getElementById('rgcet-messages');
    const inputField = document.getElementById('rgcet-input');
    const sendBtn = document.getElementById('rgcet-send-btn');
    const micBtn = document.getElementById('rgcet-mic-btn');
    const faqItems = document.querySelectorAll('.rgcet-faq-item');

    // Toggle panel visibility
    function openPanel() {
        panel.classList.remove('rgcet-hidden');
        launcher.classList.add('rgcet-hidden');
        // Give focus to input slightly after opening
        setTimeout(() => inputField.focus(), 300);
    }

    function closePanel() {
        panel.classList.add('rgcet-hidden');
        launcher.classList.remove('rgcet-hidden');
    }

    // Event Listeners
    launcher.addEventListener('click', openPanel);
    closeBtn.addEventListener('click', closePanel);

    // Scroll to bottom of message area
    function scrollToBottom() {
        messagesArea.scrollTo({
            top: messagesArea.scrollHeight,
            behavior: 'smooth'
        });
    }

    // Add user message to UI
    function addUserMessage(text) {
        if (!text.trim()) return;

        const msgDiv = document.createElement('div');
        msgDiv.className = 'rgcet-msg rgcet-msg-user';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'rgcet-msg-content';
        contentDiv.textContent = text;
        
        msgDiv.appendChild(contentDiv);
        messagesArea.appendChild(msgDiv);
        scrollToBottom();
    }

    function appendTextWithLinks(container, text) {
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        const parts = String(text).split(urlRegex);

        parts.forEach((part, index) => {
            if (!part) {
                return;
            }

            if (index % 2 === 1) {
                const link = document.createElement('a');
                link.href = part;
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
                link.textContent = part;
                link.className = 'rgcet-msg-link';
                container.appendChild(link);
                return;
            }

            container.appendChild(document.createTextNode(part));
        });
    }

    // Add bot typing indicator
    function showTypingIndicator() {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'rgcet-msg rgcet-msg-bot rgcet-typing-msg';
        msgDiv.id = 'rgcet-typing-indicator';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'rgcet-msg-content';
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'rgcet-typing-indicator';
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            dot.className = 'rgcet-typing-dot';
            typingDiv.appendChild(dot);
        }
        
        contentDiv.appendChild(typingDiv);
        msgDiv.appendChild(contentDiv);
        messagesArea.appendChild(msgDiv);
        scrollToBottom();
        
        return msgDiv;
    }

    // Remove typing indicator
    function removeTypingIndicator() {
        const indicator = document.getElementById('rgcet-typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    // Add bot message
    function addBotMessage(text, isFallback = false) {
        removeTypingIndicator();
        
        const msgDiv = document.createElement('div');
        msgDiv.className = `rgcet-msg rgcet-msg-bot ${isFallback ? 'rgcet-fallback' : ''}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'rgcet-msg-content';
        appendTextWithLinks(contentDiv, text);
        
        msgDiv.appendChild(contentDiv);
        messagesArea.appendChild(msgDiv);
        scrollToBottom();
    }

    // Fetch bot response from backend API
    async function fetchBotResponse(userText) {
        showTypingIndicator();
        
        // Disable input while typing
        inputField.disabled = true;
        sendBtn.disabled = true;

        try {
            const response = await fetch(`${API_BASE_URL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userText })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            inputField.disabled = false;
            sendBtn.disabled = false;

            const answer = data.answer || "I could not find an answer to your question.";
            const isFallback = data.fallback_type === 'generic';
            
            addBotMessage(answer, isFallback);

        } catch (error) {
            console.error('Widget API Error:', error);
            inputField.disabled = false;
            sendBtn.disabled = false;
            
            // Part D - Error handling
            addBotMessage("The assistant is temporarily unavailable. Please try again later.", true);
        } finally {
            inputField.focus();
        }
    }

    // Handle sending message
    function handleSend() {
        const text = inputField.value.trim();
        if (!text) return;
        
        addUserMessage(text);
        inputField.value = '';
        inputField.style.height = 'auto'; // Reset height if dynamic
        
        // Send to backend API
        fetchBotResponse(text);
    }

    // Input Events
    sendBtn.addEventListener('click', handleSend);
    
    inputField.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleSend();
        }
    });

    // Check input to toggle send button state (optional logic)
    inputField.addEventListener('input', () => {
        if (inputField.value.trim()) {
            sendBtn.style.opacity = '1';
        } else {
            sendBtn.style.opacity = '0.7';
        }
    });

    // FAQ clicks
    faqItems.forEach(item => {
        item.addEventListener('click', () => {
            const text = item.querySelector('.rgcet-faq-text').textContent;
            addUserMessage(text);
            fetchBotResponse(text);
        });
    });

    // Voice Input via SpeechRecognition API
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition && micBtn) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.lang = 'en-US';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        let isRecording = false;

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            inputField.value = transcript;
            inputField.dispatchEvent(new Event('input'));
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            isRecording = false;
            micBtn.style.color = '';
            inputField.disabled = false;
            sendBtn.disabled = false;
        };

        recognition.onend = () => {
            isRecording = false;
            micBtn.style.color = '';
            inputField.disabled = false;
            sendBtn.disabled = false;
        };

        micBtn.addEventListener('click', () => {
            if (isRecording) {
                recognition.stop();
            } else {
                recognition.start();
                isRecording = true;
                micBtn.style.color = '#ef4444';
                inputField.disabled = true;
                sendBtn.disabled = true;
            }
        });
    } else if (micBtn) {
        micBtn.addEventListener('click', () => {
            alert('Speech Recognition is not supported in your browser.');
        });
    }
});
