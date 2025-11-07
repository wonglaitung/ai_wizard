// 获取DOM元素
const chatTrigger = document.getElementById('chat-trigger');
const chatContainer = document.getElementById('chat-container');
const closeChat = document.getElementById('close-chat');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const chatMessages = document.getElementById('chat-messages');
const presetButtons = document.querySelectorAll('.preset-btn');

// 显示对话框
chatTrigger.addEventListener('click', () => {
    chatContainer.classList.remove('hidden');
    userInput.focus(); // 自动聚焦到输入框
});

// 隐藏对话框
closeChat.addEventListener('click', () => {
    chatContainer.classList.add('hidden');
});

// 发送消息
sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// 预设问题按钮事件
presetButtons.forEach(button => {
    button.addEventListener('click', () => {
        const question = button.getAttribute('data-question');
        // 显示用户消息
        displayMessage(question, 'user');
        // 调用AI接口获取回复
        getAIResponse(question);
    });
});

// 发送消息函数
function sendMessage() {
    const message = userInput.value.trim();
    if (message) {
        // 显示用户消息
        displayMessage(message, 'user');
        userInput.value = ''; // 清空输入框
        
        // 调用AI接口获取回复
        getAIResponse(message);
    }
}

// 显示消息
function displayMessage(message, sender) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message');
    messageElement.classList.add(sender + '-message');
    messageElement.textContent = message;
    chatMessages.appendChild(messageElement);
    
    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 获取AI回复
async function getAIResponse(userMessage) {
    try {
        // 显示"正在输入"提示
        let typingIndicator = displayTypingIndicator();
        
        // 调用后端API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: userMessage })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // 移除"正在输入"提示
        if (typingIndicator && typingIndicator.parentNode) {
            typingIndicator.parentNode.removeChild(typingIndicator);
        }
        
        // 创建一个新的AI消息元素用于流式显示
        const aiMessageElement = document.createElement('div');
        aiMessageElement.classList.add('message', 'ai-message');
        chatMessages.appendChild(aiMessageElement);
        
        // 处理流式响应
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let done = false;
        let aiReply = '';
        
        while (!done) {
            const { value, done: readerDone } = await reader.read();
            done = readerDone;
            
            if (value) {
                const chunk = decoder.decode(value, { stream: true });
                // 解析SSE数据
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        
                        if (data === '[DONE]') {
                            // 滚动到底部
                            chatMessages.scrollTop = chatMessages.scrollHeight;
                            return;
                        }
                        
                        try {
                            const jsonData = JSON.parse(data);
                            
                            if (jsonData.error) {
                                aiMessageElement.textContent = jsonData.error;
                                chatMessages.scrollTop = chatMessages.scrollHeight;
                                return;
                            }
                            
                            if (jsonData.reply) {
                                aiReply += jsonData.reply;
                                aiMessageElement.textContent = aiReply;
                                // 滚动到底部
                                chatMessages.scrollTop = chatMessages.scrollHeight;
                            }
                        } catch (e) {
                            console.error('Error parsing JSON:', e);
                        }
                    }
                }
            }
        }
    } catch (error) {
        // 移除"正在输入"提示
        const typingIndicator = chatMessages.querySelector('.message.ai-message');
        if (typingIndicator && typingIndicator.textContent === '正在输入...') {
            chatMessages.removeChild(typingIndicator);
        }
        
        console.error('Error:', error);
        displayMessage('抱歉，我无法回答您的问题。', 'ai');
    }
}

// 显示"正在输入"提示
function displayTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.classList.add('message', 'ai-message');
    indicator.textContent = '正在输入...';
    chatMessages.appendChild(indicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return indicator;
}