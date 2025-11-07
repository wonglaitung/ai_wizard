// 获取DOM元素
const chatTrigger = document.getElementById('chat-trigger');
const chatContainer = document.getElementById('chat-container');
const closeChat = document.getElementById('close-chat');
const clearOutput = document.getElementById('clear-output');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const chatMessages = document.getElementById('chat-messages');
const presetButtons = document.querySelectorAll('.preset-btn');
const outputToggle = document.getElementById('output-toggle');
const pageOutput = document.getElementById('page-output');
const outputMessages = document.getElementById('output-messages');

// 显示对话框
chatTrigger.addEventListener('click', () => {
    chatContainer.classList.remove('hidden');
    userInput.focus(); // 自动聚焦到输入框
});

// 隐藏对话框
closeChat.addEventListener('click', () => {
    chatContainer.classList.add('hidden');
});

// 清除页面输出内容事件
clearOutput.addEventListener('click', () => {
    if (confirm('确定要清除所有对话内容吗？')) {
        chatMessages.innerHTML = '';
        outputMessages.innerHTML = '';
    }
});

// 开关切换事件
outputToggle.addEventListener('change', () => {
    if (outputToggle.checked) {
        pageOutput.classList.remove('hidden');
    } else {
        pageOutput.classList.add('hidden');
    }
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
    // 如果开关打开，只在页面输出区域显示消息
    if (outputToggle.checked) {
        const outputMessageElement = document.createElement('div');
        outputMessageElement.classList.add('output-message');
        outputMessageElement.classList.add('output-' + sender + '-message');
        outputMessageElement.textContent = message;
        outputMessages.appendChild(outputMessageElement);
        
        // 滚动到底部
        outputMessages.scrollTop = outputMessages.scrollHeight;
    } else {
        // 如果开关关闭，只在对话框中显示消息
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        messageElement.classList.add(sender + '-message');
        messageElement.textContent = message;
        chatMessages.appendChild(messageElement);
        
        // 滚动到底部
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
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
        
        // 根据开关状态移除相应的"正在输入"提示
        if (outputToggle.checked) {
            if (typingIndicator.outputIndicator && typingIndicator.outputIndicator.parentNode) {
                typingIndicator.outputIndicator.parentNode.removeChild(typingIndicator.outputIndicator);
            }
        } else {
            if (typingIndicator.chatIndicator && typingIndicator.chatIndicator.parentNode) {
                typingIndicator.chatIndicator.parentNode.removeChild(typingIndicator.chatIndicator);
            }
        }
        
        // 根据开关状态决定在哪里创建AI消息元素
        let aiMessageElement, outputAiMessageElement;
        
        if (outputToggle.checked) {
            // 如果开关打开，只在页面输出区域创建AI消息元素
            outputAiMessageElement = document.createElement('div');
            outputAiMessageElement.classList.add('output-message', 'output-ai-message');
            outputMessages.appendChild(outputAiMessageElement);
        } else {
            // 如果开关关闭，只在对话框中创建AI消息元素
            aiMessageElement = document.createElement('div');
            aiMessageElement.classList.add('message', 'ai-message');
            chatMessages.appendChild(aiMessageElement);
        }
        
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
                            if (outputToggle.checked) {
                                outputMessages.scrollTop = outputMessages.scrollHeight;
                            } else {
                                chatMessages.scrollTop = chatMessages.scrollHeight;
                            }
                            return;
                        }
                        
                        try {
                            const jsonData = JSON.parse(data);
                            
                            if (jsonData.error) {
                                if (outputToggle.checked && outputAiMessageElement) {
                                    outputAiMessageElement.textContent = jsonData.error;
                                    outputMessages.scrollTop = outputMessages.scrollHeight;
                                } else if (aiMessageElement) {
                                    aiMessageElement.textContent = jsonData.error;
                                    chatMessages.scrollTop = chatMessages.scrollHeight;
                                }
                                return;
                            }
                            
                            if (jsonData.reply) {
                                aiReply += jsonData.reply;
                                
                                // 根据开关状态更新相应的消息元素
                                if (outputToggle.checked && outputAiMessageElement) {
                                    outputAiMessageElement.textContent = aiReply;
                                    outputMessages.scrollTop = outputMessages.scrollHeight;
                                } else if (aiMessageElement) {
                                    aiMessageElement.textContent = aiReply;
                                    chatMessages.scrollTop = chatMessages.scrollHeight;
                                }
                            }
                        } catch (e) {
                            console.error('Error parsing JSON:', e);
                        }
                    }
                }
            }
        }
    } catch (error) {
        // 根据开关状态移除相应的"正在输入"提示
        if (outputToggle.checked) {
            const outputTypingIndicator = outputMessages.querySelector('.output-ai-message');
            if (outputTypingIndicator && outputTypingIndicator.textContent === '正在输入...') {
                outputMessages.removeChild(outputTypingIndicator);
            }
        } else {
            const chatTypingIndicator = chatMessages.querySelector('.message.ai-message');
            if (chatTypingIndicator && chatTypingIndicator.textContent === '正在输入...') {
                chatMessages.removeChild(chatTypingIndicator);
            }
        }
        
        console.error('Error:', error);
        displayMessage('抱歉，我无法回答您的问题。', 'ai');
    }
}

// 显示"正在输入"提示
function displayTypingIndicator() {
    let chatIndicator, outputIndicator;
    
    if (outputToggle.checked) {
        // 如果开关打开，只在页面输出区域显示"正在输入"提示
        outputIndicator = document.createElement('div');
        outputIndicator.classList.add('output-message', 'output-ai-message');
        outputIndicator.textContent = '正在输入...';
        outputMessages.appendChild(outputIndicator);
        outputMessages.scrollTop = outputMessages.scrollHeight;
    } else {
        // 如果开关关闭，只在对话框中显示"正在输入"提示
        chatIndicator = document.createElement('div');
        chatIndicator.classList.add('message', 'ai-message');
        chatIndicator.textContent = '正在输入...';
        chatMessages.appendChild(chatIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    return { chatIndicator: chatIndicator, outputIndicator: outputIndicator };
}