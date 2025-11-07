// 获取DOM元素
const chatTrigger = document.getElementById('chat-trigger');
const chatContainer = document.getElementById('chat-container');
const closeChat = document.getElementById('close-chat');
const clearChat = document.getElementById('clear-chat');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const chatMessages = document.getElementById('chat-messages');
const presetButtons = document.querySelectorAll('.preset-btn');
const outputToggle = document.getElementById('output-toggle');
const pageOutput = document.getElementById('page-output');
const outputMessages = document.getElementById('output-messages');
const menuItems = document.querySelectorAll('.menu-item');
const pages = document.querySelectorAll('.page');
const toggleSidebarBtn = document.getElementById('toggle-sidebar');
const sidebar = document.querySelector('.sidebar');
const contentArea = document.querySelector('.content-area');

// 设置页面相关元素
const apiKeyInput = document.getElementById('api-key');
const baseUrlInput = document.getElementById('base-url');
const modelNameInput = document.getElementById('model-name');
const temperatureInput = document.getElementById('temperature');
const maxTokensInput = document.getElementById('max-tokens');
const topPInput = document.getElementById('top-p');
const frequencyPenaltyInput = document.getElementById('frequency-penalty');
const temperatureValue = document.getElementById('temperature-value');
const topPValue = document.getElementById('top-p-value');
const frequencyPenaltyValue = document.getElementById('frequency-penalty-value');
const saveSettingsBtn = document.getElementById('save-settings');

// 菜单收起功能
toggleSidebarBtn.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
    contentArea.classList.toggle('sidebar-collapsed');
    
    // 更新按钮图标
    if (sidebar.classList.contains('collapsed')) {
        toggleSidebarBtn.textContent = '▶';
    } else {
        toggleSidebarBtn.textContent = '◀';
    }
    
    // 调整页面输出区域的位置
    adjustPageOutputPosition();
});

// 页面切换功能
menuItems.forEach(item => {
    item.addEventListener('click', () => {
        // 如果菜单是收起状态，点击菜单项时展开菜单
        if (sidebar.classList.contains('collapsed')) {
            sidebar.classList.remove('collapsed');
            contentArea.classList.remove('sidebar-collapsed');
            toggleSidebarBtn.textContent = '◀';
            // 调整页面输出区域的位置
            adjustPageOutputPosition();
        }
        
        // 移除所有菜单项的激活状态
        menuItems.forEach(menuItem => menuItem.classList.remove('active'));
        // 添加激活状态到当前菜单项
        item.classList.add('active');
        
        // 隐藏所有页面
        pages.forEach(page => page.classList.remove('active'));
        
        // 显示对应页面
        const pageId = item.getAttribute('data-page') + '-page';
        const targetPage = document.getElementById(pageId);
        if (targetPage) {
            targetPage.classList.add('active');
        }
    });
});

// 调整页面输出区域位置的函数
function adjustPageOutputPosition() {
    if (pageOutput) {
        if (sidebar.classList.contains('collapsed')) {
            // 菜单收起时，页面输出区域左边距减少
            pageOutput.style.left = '80px';
        } else {
            // 菜单展开时，页面输出区域左边距增加
            pageOutput.style.left = '270px';
        }
    }
}

// 显示对话框
chatTrigger.addEventListener('click', () => {
    chatContainer.classList.remove('hidden');
    userInput.focus(); // 自动聚焦到输入框
});

// 隐藏对话框
closeChat.addEventListener('click', () => {
    chatContainer.classList.add('hidden');
});

// 清除对话框内容事件
if (clearChat) {
    clearChat.addEventListener('click', () => {
        if (confirm('确定要清除所有对话内容吗？')) {
            // 清除对话框中的内容
            if (chatMessages) {
                chatMessages.innerHTML = '';
            }
            
            // 如果页面输出区域是开启的，也清除页面输出区域的内容
            if (outputMessages) {
                outputMessages.innerHTML = '';
            }
        }
    });
}

// 设置页面功能
// 更新滑块值显示
temperatureInput.addEventListener('input', () => {
    temperatureValue.textContent = temperatureInput.value;
});

topPInput.addEventListener('input', () => {
    topPValue.textContent = topPInput.value;
});

frequencyPenaltyInput.addEventListener('input', () => {
    frequencyPenaltyValue.textContent = frequencyPenaltyInput.value;
});

// 保存设置
saveSettingsBtn.addEventListener('click', () => {
    const settings = {
        apiKey: apiKeyInput.value,
        baseUrl: baseUrlInput.value,
        modelName: modelNameInput.value,
        temperature: parseFloat(temperatureInput.value),
        maxTokens: parseInt(maxTokensInput.value),
        topP: parseFloat(topPInput.value),
        frequencyPenalty: parseFloat(frequencyPenaltyInput.value)
    };
    
    // 保存到本地存储
    localStorage.setItem('aiSettings', JSON.stringify(settings));
    
    alert('设置已保存！');
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
        
        // 获取保存的设置
        let settings = {
            modelName: 'qwen-max',
            temperature: 0.7,
            maxTokens: 2048,
            topP: 0.9,
            frequencyPenalty: 0.5,
            baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1'  // 默认URL
        };
        
        const savedSettings = localStorage.getItem('aiSettings');
        if (savedSettings) {
            settings = {...settings, ...JSON.parse(savedSettings)};
        }
        
        // 调用后端API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                message: userMessage,
                settings: settings
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // 移除"正在输入"提示
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
        // 移除"正在输入"提示
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