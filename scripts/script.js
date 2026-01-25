// 获取DOM元素 - 只有在元素存在的情况下才获取
let chatTrigger, chatContainer, closeChat, clearChat, userInput, sendBtn, chatMessages, presetButtons, outputToggle, pageOutput, outputMessages, menuItems, pages, toggleSidebarBtn, sidebar, contentArea, fileUploadInput, fileNameSpan, clearFileBtn;

// 配置页面相关元素
let apiKeyInput, toggleApiKeyBtn, baseUrlInput, modelNameInput, temperatureInput, temperatureValue, maxTokensInput, topPInput, topPValue, frequencyPenaltyInput, frequencyPenaltyValue, saveConfigBtn, resetConfigBtn;

// 全局变量
let pendingMessage = null; // 用于存储排队的消息
let uploadedFileId = ''; // 用于存储上传文件的ID
let chatHistory = []; // 聊天历史记录
let uploadedFileContent = ''; // 存储上传的文件内容

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM内容加载完成');
    chatTrigger = document.getElementById('chat-trigger');
    chatContainer = document.getElementById('chat-container');
    closeChat = document.getElementById('close-chat');
    clearChat = document.getElementById('clear-chat');
    userInput = document.getElementById('user-input');
    sendBtn = document.getElementById('send-btn');
    chatMessages = document.getElementById('chat-messages');
    presetButtons = document.querySelectorAll('.preset-btn');
    outputToggle = document.getElementById('output-toggle');
    pageOutput = document.getElementById('page-output');
    outputMessages = document.getElementById('output-messages');
    menuItems = document.querySelectorAll('.menu-item');
    pages = document.querySelectorAll('.page');
    toggleSidebarBtn = document.getElementById('toggle-sidebar');
    sidebar = document.querySelector('.sidebar');
    contentArea = document.querySelector('.content-area');
    fileUploadInput = document.getElementById('file-upload');
    fileNameSpan = document.getElementById('file-name');
    clearFileBtn = document.getElementById('clear-file');
    
    // 配置页面相关元素
    apiKeyInput = document.getElementById('api-key');
    toggleApiKeyBtn = document.getElementById('toggle-api-key');
    baseUrlInput = document.getElementById('base-url');
    modelNameInput = document.getElementById('model-name');
    temperatureInput = document.getElementById('temperature');
    temperatureValue = document.getElementById('temperature-value');
    maxTokensInput = document.getElementById('max-tokens');
    topPInput = document.getElementById('top-p');
    topPValue = document.getElementById('top-p-value');
    frequencyPenaltyInput = document.getElementById('frequency-penalty');
    frequencyPenaltyValue = document.getElementById('frequency-penalty-value');
    saveConfigBtn = document.getElementById('save-config');
    resetConfigBtn = document.getElementById('reset-config');
    
    console.log('获取到的元素:', {userInput, sendBtn, apiKeyInput, saveConfigBtn});
    
    // 初始化清除按钮状态
    if (clearFileBtn) {
        clearFileBtn.style.display = 'none';
    }

    // 菜单收起功能
    if (toggleSidebarBtn) {
        toggleSidebarBtn.addEventListener('click', () => {
            if (sidebar && contentArea) {
                sidebar.classList.toggle('collapsed');
                contentArea.classList.toggle('sidebar-collapsed');
                
                // 更新按钮图标
                if (sidebar.classList.contains('collapsed')) {
                    toggleSidebarBtn.textContent = '▶';
                } else {
                    toggleSidebarBtn.textContent = '◀';
                }
                
                // 调整图表输出区域的位置
                adjustPageOutputPosition();
            }
        });
    }

    // 文件上传处理
    if (fileUploadInput && fileNameSpan && clearFileBtn) {
        fileUploadInput.addEventListener('change', async (event) => {
            const file = event.target.files[0];
            if (file) {
                // 显示上传图标
                fileNameSpan.innerHTML = `<span class="upload-icon">📤</span> ${file.name}`;
                // 显示清除按钮
                clearFileBtn.style.display = 'block';
                
                // 创建FormData对象用于上传文件
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    // 上传文件到服务器
                    const response = await fetch('/api/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok && result.status === 'success') {
                        // 保存文件内容和文件ID
                        uploadedFileContent = result.file_content;
                        uploadedFileId = result.file_id; // 保存文件ID用于后续数据处理
                        
                        // 检查文件内容的token数量
                        const tokenCount = estimateTokenCount(result.file_content);
                        // 从配置中获取最大Token数
                        const savedSettings = localStorage.getItem('aiSettings');
                        let maxTokens = 8196; // 默认值
                        if (savedSettings) {
                            const settings = JSON.parse(savedSettings);
                            maxTokens = settings.maxTokens || 8196;
                        }
                        
                        if (tokenCount > maxTokens) {
                            // 显示警告信息
                            fileNameSpan.innerHTML = `<span style="color: #ff6b35; font-weight: bold;">⚠️ ${file.name} (约${tokenCount} tokens - 可能超出限制)</span>`;
                            // 添加一个提示信息
                            alert(`文件 "${file.name}" 的内容可能超出最大Token限制（约${tokenCount} tokens，最大限制为${maxTokens}）。向大模型发送时可能失败。`);
                        } else {
                            fileNameSpan.textContent = file.name; // 上传成功后显示文件名
                        }
                        
                        // 自动打开图表输出开关
                        if (outputToggle && !outputToggle.checked) {
                            outputToggle.checked = true;
                            // 触发change事件以确保UI更新
                            outputToggle.dispatchEvent(new Event('change'));
                        }
                        
                        console.log('文件上传成功，file_id:', uploadedFileId);
                        
                        // 如果有排队的消息，现在发送它
                        if (pendingMessage) {
                            console.log('处理排队的消息:', pendingMessage);
                            const messageToProcess = pendingMessage;
                            pendingMessage = null; // 清空排队的消息
                            
                            // 显示用户消息并调用AI接口
                            displayMessage(messageToProcess, 'user');
                            
                            // 调用AI接口获取回复
                            getAIResponse(messageToProcess);
                        }
                    } else {
                        console.error(`文件上传失败: ${result.error || '未知错误'}`);
                        uploadedFileContent = '';
                        uploadedFileId = ''; // 清空文件ID
                        fileNameSpan.textContent = '文件上传失败';
                        clearFileBtn.style.display = 'none';
                    }
                } catch (error) {
                    console.error('文件上传错误:', error);
                    uploadedFileContent = '';
                    fileNameSpan.textContent = '文件上传失败';
                    clearFileBtn.style.display = 'none';
                }
            } else {
                fileNameSpan.textContent = '未选择文件';
                uploadedFileContent = '';
                clearFileBtn.style.display = 'none';
            }
        });
    }

    // 清除文件按钮处理
    if (clearFileBtn && fileNameSpan) {
        clearFileBtn.addEventListener('click', (event) => {
            event.preventDefault();
            // 重置文件输入
            if (fileUploadInput) fileUploadInput.value = '';
            // 重置文件名显示
            fileNameSpan.textContent = '未选择文件';
            // 清空上传的文件内容、文件ID和排队的消息
            uploadedFileContent = '';
            uploadedFileId = '';
            pendingMessage = null;
            // 隐藏清除按钮
            clearFileBtn.style.display = 'none';
        });
    }

    // 页面切换功能
    if (menuItems && pages) {
        menuItems.forEach(item => {
            item.addEventListener('click', () => {
                console.log('菜单项被点击:', item.getAttribute('data-page'));
                
                // 如果菜单是收起状态，点击菜单项时展开菜单
                if (sidebar && sidebar.classList.contains('collapsed')) {
                    sidebar.classList.remove('collapsed');
                    contentArea.classList.remove('sidebar-collapsed');
                    if (toggleSidebarBtn) toggleSidebarBtn.textContent = '◀';
                    // 调整图表输出区域的位置
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
                console.log('目标页面ID:', pageId);
                const targetPage = document.getElementById(pageId);
                if (targetPage) {
                    console.log('找到目标页面:', targetPage);
                    targetPage.classList.add('active');
                    console.log('页面已激活:', targetPage.classList.contains('active'));
                    
                    // 如果是其他页面，确保显示图表输出区域的开关
                    if (outputToggle) {
                        // 不改变开关状态，让用户可以控制
                    }
                } else {
                    console.log('未找到目标页面:', pageId);
                }
            });
        });
    }

    // 切换对话框显示/隐藏
    if (chatTrigger) {
        chatTrigger.addEventListener('click', () => {
            if (chatContainer) {
                if (chatContainer.classList.contains('hidden')) {
                    // 如果对话框是隐藏的，显示它
                    chatContainer.classList.remove('hidden');
                    if (userInput) userInput.focus(); // 自动聚焦到输入框
                } else {
                    // 如果对话框是显示的，隐藏它
                    chatContainer.classList.add('hidden');
                }
            }
        });
    }

    // 隐藏对话框
    if (closeChat) {
        closeChat.addEventListener('click', () => {
            if (chatContainer) chatContainer.classList.add('hidden');
        });
    }

    // 清除对话框内容事件
    if (clearChat) {
        clearChat.addEventListener('click', () => {
            if (confirm('确定要清除所有对话内容吗？')) {
                // 清除对话框中的内容
                if (chatMessages) {
                    chatMessages.innerHTML = '';
                }
                
                // 如果图表输出区域是开启的，也清除图表输出区域的内容
                if (outputMessages) {
                    outputMessages.innerHTML = '';
                }
                
                // 清除聊天历史记录
                chatHistory = [];
            }
        });
    }

    // 开关切换事件
    if (outputToggle) {
        outputToggle.addEventListener('change', () => {
            console.log('输出开关状态改变:', outputToggle.checked);
            if (outputToggle.checked) {
                if (pageOutput) pageOutput.classList.remove('hidden');
                console.log('图表输出区域已显示');
            } else {
                if (pageOutput) pageOutput.classList.add('hidden');
                console.log('图表输出区域已隐藏');
            }
        });
    }

    // 发送消息
    if (sendBtn) {
        console.log('绑定发送按钮事件');
        sendBtn.addEventListener('click', () => {
            console.log('发送按钮被点击');
            sendMessage();
        });
    }
    if (userInput) {
        userInput.addEventListener('keypress', (e) => {
            console.log('按键事件:', e.key);
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }

    // 预设问题按钮事件
    if (presetButtons) {
        presetButtons.forEach(button => {
            button.addEventListener('click', () => {
                const question = button.getAttribute('data-question');
                
                // 将问题放入输入框
                userInput.value = question;
                // 聚焦到输入框
                userInput.focus();
            });
        });
    }
    
    // 加载保存的配置
    loadConfig();
    
    // API密钥显示/隐藏切换
    if (toggleApiKeyBtn && apiKeyInput) {
        toggleApiKeyBtn.addEventListener('click', function() {
            if (apiKeyInput.type === 'password') {
                apiKeyInput.type = 'text';
                toggleApiKeyBtn.textContent = '🙈';
            } else {
                apiKeyInput.type = 'password';
                toggleApiKeyBtn.textContent = '👁️';
            }
        });
    }
    
    // 滑块值显示
    if (temperatureInput && temperatureValue) {
        temperatureInput.addEventListener('input', function() {
            temperatureValue.textContent = this.value;
        });
    }
    
    if (topPInput && topPValue) {
        topPInput.addEventListener('input', function() {
            topPValue.textContent = this.value;
        });
    }
    
    if (frequencyPenaltyInput && frequencyPenaltyValue) {
        frequencyPenaltyInput.addEventListener('input', function() {
            frequencyPenaltyValue.textContent = this.value;
        });
    }
    
    // 保存配置
    if (saveConfigBtn) {
        saveConfigBtn.addEventListener('click', function() {
            saveConfig();
            alert('配置已保存！');
        });
    }
    
    // 重置配置
    if (resetConfigBtn) {
        resetConfigBtn.addEventListener('click', function() {
            resetConfig();
            alert('配置已重置为默认值！');
        });
    }
    
    // 为下载Word按钮添加事件监听器
    const downloadWordBtn = document.getElementById('download-word');
    if (downloadWordBtn) {
        downloadWordBtn.addEventListener('click', exportToWord);
    }
    
    // 智能评估页面相关元素
    const startEvaluationBtn = document.getElementById('start-evaluation');
    const clearEvaluationBtn = document.getElementById('clear-evaluation');
    const closeResultsBtn = document.getElementById('close-results');
    const evaluationResults = document.getElementById('evaluation-results');
    const resultsContent = document.getElementById('results-content');
    
    // 开始评估按钮事件
    if (startEvaluationBtn) {
        startEvaluationBtn.addEventListener('click', startEvaluation);
    }
    
    // 清除评估结果按钮事件
    if (clearEvaluationBtn) {
        clearEvaluationBtn.addEventListener('click', clearEvaluationResults);
    }
    
    // 关闭结果按钮事件
    if (closeResultsBtn) {
        closeResultsBtn.addEventListener('click', function() {
            if (evaluationResults) {
                evaluationResults.classList.add('hidden');
            }
        });
    }
});

// 估算文本token数量的函数（改进版）
function estimateTokenCount(text) {
    // 这是一个改进的估算方法，更接近实际的token计算
    if (!text) return 0;
    
    // 移除多余的空白字符
    const cleanText = text.replace(/\s+/g, ' ').trim();
    
    // 更精确的token估算方法
    // 基于英文和中文混合文本的经验估算
    let tokenCount = 0;
    
    // 对于英文文本，大约每4个字符为1个token
    // 对于中文文本，每个汉字大约为1-2个token
    for (let i = 0; i < cleanText.length; i++) {
        const char = cleanText[i];
        // 检查是否为中文字符
        if (/[\u4e00-\u9fa5]/.test(char)) {
            // 中文字符计为1.5个token
            tokenCount += 1.5;
        } else if (/\s/.test(char)) {
            // 空白字符计为0.25个token
            tokenCount += 0.25;
        } else {
            // 其他字符（英文、数字、符号）计为0.25个token
            tokenCount += 0.25;
        }
    }
    
    return Math.ceil(tokenCount);
}

// 调整图表输出区域位置的函数
function adjustPageOutputPosition() {
    if (pageOutput) {
        // 保存当前的宽度和高度（如果用户已经调整过）
        const currentWidth = pageOutput.style.width;
        const currentHeight = pageOutput.style.height;
        
        if (sidebar.classList.contains('collapsed')) {
            // 菜单收起时，图表输出区域左边距减少
            pageOutput.style.left = '80px';
        } else {
            // 菜单展开时，图表输出区域左边距增加
            pageOutput.style.left = '270px';
        }
        
        // 恢复用户调整的宽度和高度（如果有的话）
        if (currentWidth) {
            pageOutput.style.width = currentWidth;
        }
        if (currentHeight) {
            pageOutput.style.height = currentHeight;
        }
    }
}

// 发送消息函数
function sendMessage() {
    const message = userInput.value.trim();
    if (message) {
        // 检查文件内容的token数（如果有的话）
        if (uploadedFileContent) {
            const fileTokenCount = estimateTokenCount(uploadedFileContent);
            console.log('估算文件Token数:', fileTokenCount);
            const messageTokenCount = estimateTokenCount(message);
            console.log('估算消息Token数:', messageTokenCount);
            const totalTokenCount = fileTokenCount + messageTokenCount;
            // 从配置中获取最大Token数
            const savedSettings = localStorage.getItem('aiSettings');
            let maxTokens = 8196; // 默认值
            if (savedSettings) {
                const settings = JSON.parse(savedSettings);
                maxTokens = settings.maxTokens || 8196;
            }
            
            if (totalTokenCount > maxTokens) {
                if (confirm(`警告：您的消息和文件内容的总token数约为${totalTokenCount}，超出最大限制${maxTokens}。向大模型发送时可能失败。是否继续发送？`)) {
                    // 显示用户消息
                    displayMessage(message, 'user');
                    userInput.value = ''; // 清空输入框
                    
                    // 调用AI接口获取回复
                    getAIResponse(message);
                }
                return; // 如果用户取消，则不发送消息
            }
        }
        
        // 显示用户消息
        displayMessage(message, 'user');
        userInput.value = ''; // 清空输入框
        
        // 调用AI接口获取回复
        getAIResponse(message);
    }
}

// 显示消息
function displayMessage(message, sender) {
    console.log('显示消息:', message, '发送者:', sender);
    // 将消息添加到聊天历史记录
    chatHistory.push({ role: sender, content: message });
    
    // 如果开关打开，只在图表输出区域显示消息
    if (outputToggle.checked) {
        console.log('在图表输出区域显示消息');
        const outputMessageElement = document.createElement('div');
        outputMessageElement.classList.add('output-message');
        outputMessageElement.classList.add('output-' + sender + '-message');
        
        // 使用marked.js渲染Markdown
        if (typeof marked !== 'undefined') {
            outputMessageElement.innerHTML = marked.parse(message);
        } else {
            outputMessageElement.textContent = message;
        }
        
        outputMessages.appendChild(outputMessageElement);
        
        // 滚动到底部
        outputMessages.scrollTop = outputMessages.scrollHeight;
    } else {
        console.log('在对话框中显示消息');
        // 如果开关关闭，只在对话框中显示消息
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        messageElement.classList.add(sender + '-message');
        
        // 使用marked.js渲染Markdown
        if (typeof marked !== 'undefined') {
            messageElement.innerHTML = marked.parse(message);
        } else {
            messageElement.textContent = message;
        }
        
        chatMessages.appendChild(messageElement);
        
        // 滚动到底部
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// 获取AI回复
async function getAIResponse(userMessage) {
    try {
        // 显示漏斗图标
        showFunnelIndicator();
        // 显示"正在输入"提示
        let typingIndicator = displayTypingIndicator();
        
        // 获取保存的设置
        let settings = {
            modelName: 'qwen-max',
            temperature: 0.7,
            maxTokens: 8196,
            topP: 0.9,
            frequencyPenalty: 0.5,
            baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',  // 默认URL
            apiKey: ''  // API密钥
        };
        
        const savedSettings = localStorage.getItem('aiSettings');
        if (savedSettings) {
            settings = {...settings, ...JSON.parse(savedSettings)};
        }
        
        // 检查是否需要使用分步分析（例如，当用户分析数据时）
        const needsStepByStep = uploadedFileContent !== '' || 
                               (userMessage.toLowerCase().includes('分析') && 
                                (userMessage.toLowerCase().includes('数据') || 
                                 userMessage.toLowerCase().includes('统计') || 
                                 userMessage.toLowerCase().includes('计算')));
        
        // 检查输出开关状态，如果打开则添加表格输出要求
        const shouldOutputAsTable = outputToggle && outputToggle.checked;
        
        // 调用后端API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                message: userMessage,
                file_content: uploadedFileContent, // 添加上传的文件内容
                file_id: uploadedFileId, // 添加文件ID用于获取完整文件内容
                history: chatHistory,
                settings: settings,
                outputAsTable: shouldOutputAsTable,
                stepByStep: needsStepByStep  // 添加分步分析参数
            })
        });
        
        if (!response.ok) {
            // 隐藏漏斗图标
            hideFunnelIndicator();
            // 尝试获取详细的错误信息
            const errorText = await response.text();
            let errorMessage = `HTTP error! status: ${response.status}`;
            
            try {
                const errorData = JSON.parse(errorText);
                if (errorData && errorData.error) {
                    // 如果error是一个对象，尝试获取其中的message
                    if (typeof errorData.error === 'object' && errorData.error.message) {
                        errorMessage = `API错误 [${response.status}]: ${errorData.error.message}`;
                    } else {
                        errorMessage = `API错误 [${response.status}]: ${errorData.error}`;
                    }
                } else if (errorData && errorData.message) {
                    errorMessage = `API错误 [${response.status}]: ${errorData.message}`;
                }
            } catch (e) {
                // 如果不是JSON格式，直接使用文本
                if (errorText) {
                    errorMessage = `API错误 [${response.status}]: ${errorText}`;
                }
            }
            
            throw new Error(errorMessage);
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
            // 如果开关打开，只在图表输出区域创建AI消息元素
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
        let buffer = ''; // 添加缓冲区来处理可能被分割的数据
        
        // 添加用于分步分析的变量
        let stepResults = {};
        
        while (!done) {
            const { value, done: readerDone } = await reader.read();
            done = readerDone;
            
            if (value) {
                const chunk = decoder.decode(value, { stream: true });
                // 将新块添加到缓冲区
                buffer += chunk;
                
                // 按行分割并处理完整的SSE消息
                let lines = buffer.split('\n');
                // 保留最后一行，因为它可能不完整
                buffer = lines.pop() || '';
                
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
                            // 检查是否包含表格，如果是，尝试绘制图表
                            if (outputToggle.checked && outputAiMessageElement) {
                                checkAndRenderChart(outputAiMessageElement);
                            } else if (aiMessageElement) {
                                checkAndRenderChart(aiMessageElement);
                            }
                            // 隐藏漏斗图标
                            hideFunnelIndicator();
                            return;
                        }
                        
                        try {
                            // 首先检查data是否为空或不完整
                            if (!data || data.trim() === '') {
                                console.warn('收到空的JSON数据，跳过处理');
                                continue;
                            }
                            
                            let jsonData;
                            try {
                                jsonData = JSON.parse(data);
                            } catch (parseError) {
                                console.error('JSON解析失败:', parseError, 'Raw data:', data);
                                continue; // 跳过这个无法解析的数据块
                            }
                            
                            if (jsonData.error) {
                                if (outputToggle.checked && outputAiMessageElement) {
                                    if (typeof marked !== 'undefined') {
                                        outputAiMessageElement.innerHTML = marked.parse(jsonData.error);
                                    } else {
                                        outputAiMessageElement.textContent = jsonData.error;
                                    }
                                    outputMessages.scrollTop = outputMessages.scrollHeight;
                                } else if (aiMessageElement) {
                                    if (typeof marked !== 'undefined') {
                                        aiMessageElement.innerHTML = marked.parse(jsonData.error);
                                    } else {
                                        aiMessageElement.textContent = jsonData.error;
                                    }
                                    chatMessages.scrollTop = chatMessages.scrollHeight;
                                }
                                // 隐藏漏斗图标
                                hideFunnelIndicator();
                                return;
                            }
                            
                            // 使用统一的处理函数处理分步分析响应和传统响应
                            const result = handleResponseData(jsonData, outputAiMessageElement, aiMessageElement, aiReply, stepResults);
                            if (result.aiReplyUpdated) {
                                aiReply = result.aiReply;
                            }
                            if (result.stepResultsUpdated) {
                                stepResults = result.stepResults;
                            }
                        } catch (e) {
                            console.error('Error parsing JSON:', e, 'Raw data:', data);
                            // 尝试解析数据中的错误信息
                            if (data && data.includes('error')) {
                                try {
                                    // 尝试从可能的部分JSON中提取错误信息
                                    const errorMatch = data.match(/"error"[^}]*"([^"]*)"/);
                                    if (errorMatch) {
                                        const errorMessage = errorMatch[1];
                                        if (outputToggle.checked && outputAiMessageElement) {
                                            outputAiMessageElement.textContent = `错误: ${errorMessage}`;
                                        } else if (aiMessageElement) {
                                            aiMessageElement.textContent = `错误: ${errorMessage}`;
                                        }
                                    }
                                } catch (innerError) {
                                    console.error('无法从错误数据中提取错误信息:', innerError);
                                }
                            }
                        }
                    }
                }
            }
        }
        
        // 处理缓冲区中可能剩余的数据
        if (buffer.trim() !== '') {
            // 添加缓冲区内容到行数组进行处理
            const remainingLines = [buffer];
            for (const line of remainingLines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    
                    if (data === '[DONE]') {
                        // 滚动到底部
                        if (outputToggle.checked) {
                            outputMessages.scrollTop = outputMessages.scrollHeight;
                        } else {
                            chatMessages.scrollTop = chatMessages.scrollHeight;
                        }
                        // 检查是否包含表格，如果是，尝试绘制图表
                        if (outputToggle.checked && outputAiMessageElement) {
                            checkAndRenderChart(outputAiMessageElement);
                        } else if (aiMessageElement) {
                            checkAndRenderChart(aiMessageElement);
                        }
                        return;
                    }
                    
                    try {
                        // 首先检查data是否为空或不完整
                        if (!data || data.trim() === '') {
                            console.warn('收到空的JSON数据，跳过处理');
                            continue;
                        }
                        
                        let jsonData;
                        try {
                            jsonData = JSON.parse(data);
                        } catch (parseError) {
                            console.error('JSON解析失败:', parseError, 'Raw data:', data);
                            continue; // 跳过这个无法解析的数据块
                        }
                        
                        if (jsonData.error) {
                            if (outputToggle.checked && outputAiMessageElement) {
                                if (typeof marked !== 'undefined') {
                                    outputAiMessageElement.innerHTML = marked.parse(jsonData.error);
                                } else {
                                    outputAiMessageElement.textContent = jsonData.error;
                                }
                                outputMessages.scrollTop = outputMessages.scrollHeight;
                            } else if (aiMessageElement) {
                                if (typeof marked !== 'undefined') {
                                    aiMessageElement.innerHTML = marked.parse(jsonData.error);
                                } else {
                                    aiMessageElement.textContent = jsonData.error;
                                }
                                chatMessages.scrollTop = chatMessages.scrollHeight;
                            }
                            return;
                        }
                        
                        // 使用统一的处理函数处理分步分析响应和传统响应
                        const result = handleResponseData(jsonData, outputAiMessageElement, aiMessageElement, aiReply, stepResults);
                        if (result.aiReplyUpdated) {
                            aiReply = result.aiReply;
                        }
                        if (result.stepResultsUpdated) {
                            stepResults = result.stepResults;
                        }
                    } catch (e) {
                        console.error('Error parsing JSON:', e, 'Raw data:', data);
                        // 尝试解析数据中的错误信息
                        if (data && data.includes('error')) {
                            try {
                                // 尝试从可能的部分JSON中提取错误信息
                                const errorMatch = data.match(/"error"[^}]*"([^"]*)"/);
                                if (errorMatch) {
                                    const errorMessage = errorMatch[1];
                                    if (outputToggle.checked && outputAiMessageElement) {
                                        outputAiMessageElement.textContent = `错误: ${errorMessage}`;
                                    } else if (aiMessageElement) {
                                        aiMessageElement.textContent = `错误: ${errorMessage}`;
                                    }
                                }
                            } catch (innerError) {
                                console.error('无法从错误数据中提取错误信息:', innerError);
                            }
                        }
                    }
                }
            }
        }
    } catch (error) {
        // 隐藏漏斗图标
        hideFunnelIndicator();
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
        // 显示详细的错误信息
        displayMessage(`错误: ${error.message}`, 'ai');
    }
}

// 检查是否包含表格并渲染图表
function checkAndRenderChart(messageElement) {
    // 获取所有表格元素
    const tableElements = messageElement.querySelectorAll('table');
    
    // 为每个表格创建对应的图表
    tableElements.forEach((tableElement, index) => {
        // 解析表格数据
        const tableData = parseTableData(tableElement);
        if (tableData) {
            // 创建图表包装容器
            const chartWrapper = document.createElement('div');
            chartWrapper.className = 'chart-wrapper';
            chartWrapper.style.width = '100%';
            chartWrapper.style.marginTop = '20px';
            
            // 创建图表类型选择控件
            const chartControls = document.createElement('div');
            chartControls.className = 'chart-controls';
            
            // 创建左侧控件容器
            const leftControls = document.createElement('div');
            leftControls.className = 'chart-controls-left';
            leftControls.innerHTML = `
                <label for="chart-type-${index}">图表类型: </label>
                <select id="chart-type-${index}" class="chart-type-selector">
                    <option value="bar">柱状图</option>
                    <option value="line">折线图</option>
                    <option value="pie">饼图</option>
                    <option value="doughnut">环形图</option>
                </select>
            `;
            
            // 创建右侧控件容器
            const rightControls = document.createElement('div');
            rightControls.className = 'chart-controls-right';
            
            // 创建导出按钮
            const exportButton = document.createElement('button');
            exportButton.className = 'export-chart-btn';
            exportButton.innerHTML = '📥'; // 使用图标表示导出
            exportButton.title = '导出图表为图片';
            exportButton.addEventListener('click', function() {
                exportChartAsImage(canvas);
            });
            
            // 将控件添加到容器中
            rightControls.appendChild(exportButton);
            chartControls.appendChild(leftControls);
            chartControls.appendChild(rightControls);
            
            chartWrapper.appendChild(chartControls);
            
            // 创建图表容器
            const chartContainer = document.createElement('div');
            chartContainer.className = 'chart-container';
            chartContainer.style.width = '100%';
            chartContainer.style.height = '400px';
            
            // 创建canvas元素用于图表
            const canvas = document.createElement('canvas');
            canvas.id = 'chart-' + Date.now() + '-' + index; // 使用时间戳和索引确保唯一ID
            canvas.className = 'chart-canvas';
            chartContainer.appendChild(canvas);
            chartWrapper.appendChild(chartContainer);
            
            // 将图表包装容器插入到表格之后
            tableElement.parentNode.insertBefore(chartWrapper, tableElement.nextSibling);
            
            // 渲染图表
            renderChart(canvas, tableData, 'bar');
            
            // 添加图表类型切换事件监听器
            const chartTypeSelector = leftControls.querySelector('.chart-type-selector');
            chartTypeSelector.addEventListener('change', function() {
                const selectedType = this.value;
                renderChart(canvas, tableData, selectedType);
            });
        }
    });
}

// 解析表格数据
function parseTableData(table) {
    const rows = table.querySelectorAll('tr');
    if (rows.length < 2) return null; // 至少需要表头和一行数据
    
    const headers = [];
    const headerCells = rows[0].querySelectorAll('th, td');
    for (let j = 0; j < headerCells.length; j++) {
        headers.push(headerCells[j].textContent.trim());
    }
    
    const datasets = [];
    let hasNumericData = false; // 标记是否包含数字数据
    
    // 为每列创建一个数据集（跳过第一列，假设它是标签）
    for (let col = 1; col < headers.length; col++) {
        const data = [];
        let numericValuesCount = 0; // 记录数字值的数量
        
        for (let i = 1; i < rows.length; i++) {
            const cell = rows[i].querySelectorAll('th, td')[col];
            if (cell) {
                const cellText = cell.textContent.trim();
                const value = parseFloat(cellText);
                if (!isNaN(value)) {
                    data.push(value);
                    numericValuesCount++;
                } else {
                    // 如果不是数字，添加0
                    data.push(0);
                }
            } else {
                data.push(0);
            }
        }
        
        // 检查这列是否包含足够的数字数据（至少50%的数据是数字）
        if (numericValuesCount / data.length >= 0.5) {
            hasNumericData = true;
        }
        
        // 生成一个颜色
        const hue = (col * 137.508) % 360; // 使用黄金角度生成不同颜色
        const color = hslToHex(hue, 50, 50);
        
        datasets.push({
            label: headers[col],
            data: data,
            borderColor: color,
            backgroundColor: hexToRgba(color, 0.2),
            borderWidth: 2
        });
    }
    
    // 如果没有足够的数字数据，返回null，不生成图表
    if (!hasNumericData) {
        return null;
    }
    
    // 获取标签（第一列）
    const labels = [];
    for (let i = 1; i < rows.length; i++) {
        const labelCell = rows[i].querySelectorAll('th, td')[0];
        if (labelCell) {
            labels.push(labelCell.textContent.trim());
        }
    }
    
    return {
        labels: labels,
        datasets: datasets,
        headers: headers
    };
}

// 将HSL颜色转换为十六进制
function hslToHex(h, s, l) {
    h /= 360;
    s /= 100;
    l /= 100;
    
    let r, g, b;
    if (s === 0) {
        r = g = b = l;
    } else {
        const hue2rgb = (p, q, t) => {
            if (t < 0) t += 1;
            if (t > 1) t -= 1;
            if (t < 1/6) return p + (q - p) * 6 * t;
            if (t < 1/2) return q;
            if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
            return p;
        };
        
        const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        const p = 2 * l - q;
        r = hue2rgb(p, q, h + 1/3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1/3);
    }
    
    const toHex = x => {
        const hex = Math.round(x * 255).toString(16);
        return hex.length === 1 ? '0' + hex : hex;
    };
    
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

// 将十六进制颜色转换为RGBA
function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// 导出图表为图片
function exportChartAsImage(canvas) {
    // 创建一个临时的canvas元素用于绘制带背景的图表
    const tempCanvas = document.createElement('canvas');
    const tempCtx = tempCanvas.getContext('2d');
    
    // 设置临时canvas的尺寸与原canvas相同
    tempCanvas.width = canvas.width;
    tempCanvas.height = canvas.height;
    
    // 填充白色背景
    tempCtx.fillStyle = '#ffffff';
    tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
    
    // 将原canvas内容绘制到临时canvas上
    tempCtx.drawImage(canvas, 0, 0);
    
    // 获取带背景的图表base64数据URL
    const imageBase64 = tempCanvas.toDataURL('image/png');
    
    // 创建下载链接
    const link = document.createElement('a');
    link.href = imageBase64;
    link.download = 'chart-' + new Date().getTime() + '.png'; // 使用时间戳作为文件名
    
    // 触发下载
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// 渲染图表
function renderChart(canvas, tableData, chartType = 'bar') {
    // 检查是否已加载Chart.js
    if (typeof Chart === 'undefined') {
        console.error('Chart.js not loaded');
        return;
    }
    
    // 销毁已存在的图表实例（如果存在）
    if (canvas.chartInstance) {
        canvas.chartInstance.destroy();
    }
    
    // 创建新的图表配置
    const config = {
        type: chartType,
        data: {
            labels: tableData.labels,
            datasets: tableData.datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '数据可视化图表',
                    font: {
                        size: 16,
                        weight: 'bold'
                    },
                    padding: {
                        top: 10,
                        bottom: 20
                    }
                },
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            }
        },
        plugins: [{
            id: 'background',
            beforeDraw: (chart) => {
                const ctx = chart.canvas.getContext('2d');
                ctx.save();
                ctx.globalCompositeOperation = 'destination-over';
                ctx.fillStyle = 'white';
                ctx.fillRect(0, 0, chart.width, chart.height);
                ctx.restore();
            }
        }]
    };
    
    // 创建图表实例
    canvas.chartInstance = new Chart(canvas, config);
}



// 显示"正在输入"提示
function displayTypingIndicator() {
    let chatIndicator, outputIndicator;
    
    if (outputToggle.checked) {
        // 如果开关打开，只在图表输出区域显示"正在输入"提示
        outputIndicator = document.createElement('div');
        outputIndicator.classList.add('output-message', 'output-ai-message');
        outputIndicator.innerHTML = '<em>正在处理您的请求...</em>';
        
        outputMessages.appendChild(outputIndicator);
        outputMessages.scrollTop = outputMessages.scrollHeight;
    } else {
        // 如果开关关闭，只在对话框中显示"正在输入"提示
        chatIndicator = document.createElement('div');
        chatIndicator.classList.add('message', 'ai-message');
        chatIndicator.innerHTML = '<em>正在处理您的请求...</em>';
        
        chatMessages.appendChild(chatIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    return { chatIndicator: chatIndicator, outputIndicator: outputIndicator };
}

// 显示漏斗图标
function showFunnelIndicator() {
    // 创建漏斗图标元素
    const funnelElement = document.createElement('div');
    funnelElement.id = 'funnel-indicator';
    funnelElement.innerHTML = '⏳ 处理中...';
    funnelElement.style.position = 'relative';
    funnelElement.style.display = 'inline-block';
    funnelElement.style.fontSize = '14px';
    funnelElement.style.fontWeight = 'bold';
    funnelElement.style.color = '#666';
    funnelElement.style.margin = '5px 0';
    funnelElement.style.padding = '5px 10px';
    funnelElement.style.border = '1px solid #ddd';
    funnelElement.style.borderRadius = '15px';
    funnelElement.style.backgroundColor = '#f9f9f9';
    funnelElement.style.zIndex = '1000';
    
    // 检查是否在评估页面
    const evaluationPage = document.getElementById('evaluation-page');
    const resultsContent = document.getElementById('results-content');
    
    if (evaluationPage && evaluationPage.classList.contains('active') && resultsContent) {
        // 在评估页面显示
        resultsContent.appendChild(funnelElement);
        resultsContent.scrollTop = resultsContent.scrollHeight;
    } else {
        // 根据输出开关状态决定显示位置
        if (outputToggle.checked) {
            outputMessages.appendChild(funnelElement);
            outputMessages.scrollTop = outputMessages.scrollHeight;
        } else {
            chatMessages.appendChild(funnelElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }
}

// 隐藏漏斗图标
function hideFunnelIndicator() {
    const funnelElement = document.getElementById('funnel-indicator');
    if (funnelElement) {
        funnelElement.remove();
    }
}



// 加载配置
function loadConfig() {
    const savedConfig = localStorage.getItem('aiSettings');
    if (savedConfig) {
        const config = JSON.parse(savedConfig);
        
        if (apiKeyInput) apiKeyInput.value = config.apiKey || '';
        if (baseUrlInput) baseUrlInput.value = config.baseUrl || 'https://dashscope.aliyuncs.com/compatible-mode/v1';
        if (modelNameInput) modelNameInput.value = config.modelName || 'qwen-max';
        if (temperatureInput) temperatureInput.value = config.temperature || 0.7;
        if (maxTokensInput) maxTokensInput.value = config.maxTokens || 8196;
        if (topPInput) topPInput.value = config.topP || 0.9;
        if (frequencyPenaltyInput) frequencyPenaltyInput.value = config.frequencyPenalty || 0.5;
        
        // 更新滑块值显示
        if (temperatureValue) temperatureValue.textContent = config.temperature || 0.7;
        if (topPValue) topPValue.textContent = config.topP || 0.9;
        if (frequencyPenaltyValue) frequencyPenaltyValue.textContent = config.frequencyPenalty || 0.5;
    }
}

// 保存配置
function saveConfig() {
    const config = {
        apiKey: apiKeyInput ? apiKeyInput.value : '',
        baseUrl: baseUrlInput ? baseUrlInput.value : 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        modelName: modelNameInput ? modelNameInput.value : 'qwen-max',
        temperature: temperatureInput ? parseFloat(temperatureInput.value) : 0.7,
        maxTokens: maxTokensInput ? parseInt(maxTokensInput.value) : 8196,
        topP: topPInput ? parseFloat(topPInput.value) : 0.9,
        frequencyPenalty: frequencyPenaltyInput ? parseFloat(frequencyPenaltyInput.value) : 0.5
    };
    
    localStorage.setItem('aiSettings', JSON.stringify(config));
}

// 统一处理响应数据的函数，接收需要的元素作为参数
function handleResponseData(jsonData, outputAiMessageElement, aiMessageElement, currentAiReply, currentStepResults) {
    // 内部辅助函数：更新消息显示
    function updateMessageDisplay(content, isHtml = true) {
        if (outputToggle.checked && outputAiMessageElement) {
            if (isHtml && typeof marked !== 'undefined') {
                outputAiMessageElement.innerHTML = marked.parse(content);
            } else {
                outputAiMessageElement.textContent = content;
            }
            outputMessages.scrollTop = outputMessages.scrollHeight;
        } else if (aiMessageElement) {
            if (isHtml && typeof marked !== 'undefined') {
                aiMessageElement.innerHTML = marked.parse(content);
            } else {
                aiMessageElement.textContent = content;
            }
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }
    
    // 内部辅助函数：判断是否为计算结果对象
    function isComputationResult(obj) {
        return obj && 
               typeof obj === 'object' && 
               !Array.isArray(obj) && 
               obj.hasOwnProperty('results') && 
               obj.hasOwnProperty('task_type');
    }
    
    // 内部辅助函数：判断是否为最终报告对象
    function isFinalReport(obj) {
        return obj && 
               typeof obj === 'object' && 
               obj.hasOwnProperty('final_report') && 
               typeof obj.final_report === 'string';
    }
    
    let aiReply = currentAiReply; // 使用传入的值作为初始值
    let stepResults = { ...currentStepResults }; // 使用传入的 stepResults 副本
    let aiReplyUpdated = false; // 标记 aiReply 是否被更新
    let stepResultsUpdated = false; // 标记 stepResults 是否被更新
    
    // 处理分步分析的响应
    if (jsonData.step !== undefined) {
        // 如果有消息，先显示
        if (jsonData.message) {
            console.log(`步骤 ${jsonData.step}: ${jsonData.message}`);
            let displayMessage = `🔄 **步骤 ${jsonData.step}** - ${jsonData.message}`;
            updateMessageDisplay(displayMessage, true);
        }

        if (jsonData.result !== undefined) {
            // 保存该步骤的结果
            stepResults[jsonData.step] = jsonData.result;
            stepResultsUpdated = true;
            console.log(`步骤 ${jsonData.step} 完成`);

            // 根据结果类型进行处理
            if (isComputationResult(jsonData.result)) {
                // 计算结果对象：仅显示简短消息，不显示详细数据
                console.log('收到计算结果对象，等待最终报告...');
                if (jsonData.message) {
                    const progressMessage = `📈 **数据处理完成**：${jsonData.message}`;
                    updateMessageDisplay(progressMessage, true);
                }
            } else if (isFinalReport(jsonData.result)) {
                // 最终报告对象：提取并显示报告内容
                aiReply = jsonData.result.final_report;
                aiReplyUpdated = true;
                console.log('分步分析完成，显示最终报告');
                updateMessageDisplay(aiReply, true);
            } else if (typeof jsonData.result === 'string') {
                // 纯字符串结果：直接使用作为报告内容
                aiReply = jsonData.result;
                aiReplyUpdated = true;
                console.log('动态规划分析完成，显示最终报告');
                updateMessageDisplay(aiReply, true);
            } else if (typeof jsonData.result === 'object' && jsonData.result.needs_replanning !== undefined) {
                // 观察评估结果：显示评估信息
                const qualityScore = jsonData.result.quality_score;
                const feedback = jsonData.result.feedback;
                const needsReplanning = jsonData.result.needs_replanning;
                
                let message = `📊 **分析评估完成** - 质量评分: ${qualityScore}
📝 **反馈**: ${feedback}
`;
                if (needsReplanning) {
                    message += '🔄 **需要重新规划**，正在开始新迭代...';
                } else {
                    message += '✅ **分析完成**，生成最终报告...';
                }
                
                updateMessageDisplay(message, true);
            } else if (jsonData.result.task_type || jsonData.result.columns || jsonData.result.operations) {
                // 任务计划对象：显示计划信息
                const planMessage = `📋 **已制定分析计划**：${jsonData.message || '任务计划已生成'}`;
                updateMessageDisplay(planMessage, true);
            } else {
                // 其他类型的对象结果：转换为字符串显示
                aiReply = JSON.stringify(jsonData.result, null, 2);
                aiReplyUpdated = true;
                console.log('动态规划分析完成，显示最终报告');
                updateMessageDisplay(aiReply, true);
            }
        } else if (jsonData.message && jsonData.message.includes('最终报告')) {
            updateMessageDisplay(jsonData.message, true);
        } else if (!jsonData.result) {
            // 显示当前步骤的进度
            updateMessageDisplay(`已完成步骤 ${jsonData.step}，正在处理下一步...`, false);
        }
    } 
    // 处理传统响应
    else if (jsonData.reply) {
        aiReply += jsonData.reply;
        aiReplyUpdated = true;
        
        // 检测是否为工具执行结果
        if (aiReply.includes('✅') || aiReply.includes('❌')) {
            // 尝试解析工具执行结果中的URL
            const urlMatch = aiReply.match(/https?:\/\/[^\s]+/);
            
            if (urlMatch) {
                const url = urlMatch[0];
                const toolResultHtml = `
                    <div class="tool-execution-result">
                        <span class="tool-success">✅</span>
                        ${aiReply.replace(url, '').replace(/✅/g, '')}
                        <a href="${url}" target="_blank" class="tool-url-link">
                            🔗 点击打开链接
                        </a>
                    </div>
                `;
                // 直接设置innerHTML，不通过marked.js解析
                if (outputToggle.checked && outputAiMessageElement) {
                    outputAiMessageElement.innerHTML = toolResultHtml;
                    outputMessages.scrollTop = outputMessages.scrollHeight;
                } else if (aiMessageElement) {
                    aiMessageElement.innerHTML = toolResultHtml;
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
            } else {
                // 为工具执行结果添加特殊样式
                const toolResultHtml = `
                    <div class="tool-execution-result">
                        ${aiReply.replace(/✅/g, '<span class="tool-success">✅</span>')
                                 .replace(/❌/g, '<span class="tool-error">❌</span>')}
                    </div>
                `;
                // 直接设置innerHTML，不通过marked.js解析
                if (outputToggle.checked && outputAiMessageElement) {
                    outputAiMessageElement.innerHTML = toolResultHtml;
                    outputMessages.scrollTop = outputMessages.scrollHeight;
                } else if (aiMessageElement) {
                    aiMessageElement.innerHTML = toolResultHtml;
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
            }
        } else {
            updateMessageDisplay(aiReply, true);
        }
    }
    
    // 返回可能更新的值
    return { 
        aiReply: aiReply, 
        aiReplyUpdated: aiReplyUpdated,
        stepResults: stepResults,
        stepResultsUpdated: stepResultsUpdated
    };
}

// 导出图表输出区内容为Word文档
function exportToWord() {
    // 获取图表输出区域的内容
    const outputContent = document.getElementById('output-messages');
    if (!outputContent) {
        console.error('找不到输出消息区域');
        return;
    }
    
    // 创建HTML内容的副本，以便进行必要的转换
    const contentClone = outputContent.cloneNode(true);
    
    // 处理所有图表并将其转换为图片
    const chartCanvases = contentClone.querySelectorAll('canvas');
    chartCanvases.forEach(canvas => {
        // 创建一个临时canvas用于确保有白色背景
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');
        
        tempCanvas.width = canvas.width;
        tempCanvas.height = canvas.height;
        
        // 填充白色背景
        tempCtx.fillStyle = '#ffffff';
        tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
        
        // 将原canvas内容绘制到临时canvas上
        tempCtx.drawImage(canvas, 0, 0);
        
        // 将canvas转换为图片
        const img = document.createElement('img');
        img.src = tempCanvas.toDataURL('image/png');
        img.style.width = '100%';
        img.style.maxWidth = '800px';
        img.style.height = 'auto';
        
        // 替换canvas元素
        canvas.parentNode.replaceChild(img, canvas);
    });
    
    // 将内容转换为Word文档格式
    const wordContent = `
        <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/TR/REC-html40">
        <head>
            <meta charset="utf-8">
            <title>图表输出</title>
            <style>
                * { font-family: "微软雅黑", "Microsoft YaHei", SimSun, sans-serif; }
                table { border-collapse: collapse; width: 100%; margin: 10px 0; }
                table, th, td { border: 1px solid #000; }
                th, td { padding: 8px; text-align: left; }
                img { max-width: 100%; height: auto; }
            </style>
        </head>
        <body>
            <h1>AI数据分析报告</h1>
            <div>
                ${contentClone.innerHTML}
            </div>
        </body>
        </html>
    `;
    
    // 创建下载链接
    const blob = new Blob(['\ufeff', wordContent], { type: 'application/msword' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'AI数据分析报告_' + new Date().toLocaleDateString() + '.doc';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// 开始评估函数
async function startEvaluation() {
    const userQuestion = document.getElementById('user-question').value.trim();
    const evaluationCriteria = document.getElementById('evaluation-criteria').value.trim();
    const followUpRequirements = document.getElementById('follow-up-requirements').value.trim();
    
    // 输入验证
    if (!userQuestion) {
        alert('请输入用户问题');
        return;
    }
    
    // 显示结果区域
    const evaluationResults = document.getElementById('evaluation-results');
    const resultsContent = document.getElementById('results-content');
    if (evaluationResults) {
        evaluationResults.classList.remove('hidden');
    }
    if (resultsContent) {
        resultsContent.innerHTML = '';
    }
    
    // 显示漏斗图标
    showFunnelIndicator();
    
    // 添加处理中提示
    addEvaluationMessage('正在处理评估请求...', 'info');
    
    try {
        // 获取保存的设置
        let settings = {
            modelName: 'qwen-max',
            temperature: 0.7,
            maxTokens: 8196,
            topP: 0.9,
            frequencyPenalty: 0.5,
            baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
            apiKey: ''
        };
        
        const savedSettings = localStorage.getItem('aiSettings');
        if (savedSettings) {
            settings = {...settings, ...JSON.parse(savedSettings)};
        }
        
        // 调用后端API
        const response = await fetch('/api/evaluation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                userQuestion: userQuestion,
                evaluationCriteria: evaluationCriteria,
                followUpRequirements: followUpRequirements,
                settings: settings
            })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            let errorMessage = `HTTP error! status: ${response.status}`;
            
            try {
                const errorData = JSON.parse(errorText);
                if (errorData && errorData.error) {
                    errorMessage = `API错误 [${response.status}]: ${errorData.error}`;
                }
            } catch (e) {
                if (errorText) {
                    errorMessage = `API错误 [${response.status}]: ${errorText}`;
                }
            }
            
            throw new Error(errorMessage);
        }
        
        // 处理流式响应
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let done = false;
        let buffer = '';
        
        while (!done) {
            const { value, done: readerDone } = await reader.read();
            done = readerDone;
            
            if (value) {
                const chunk = decoder.decode(value, { stream: true });
                buffer += chunk;
                
                let lines = buffer.split('\n');
                buffer = lines.pop() || '';
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        
                        if (data === '[DONE]') {
                            addEvaluationMessage('评估完成！', 'success');
                            done = true;
                            hideFunnelIndicator();
                            break;
                        }
                        
                        try {
                            if (!data || data.trim() === '') {
                                continue;
                            }
                            
                            const jsonData = JSON.parse(data);
                            
                            if (jsonData.error) {
                                addEvaluationMessage(`错误: ${jsonData.error}`, 'error');
                                hideFunnelIndicator();
                                break;
                            }
                            
                            // 处理不同步骤的消息
                            handleEvaluationStep(jsonData);
                            
                        } catch (e) {
                            console.error('Error parsing JSON:', e, 'Raw data:', data);
                        }
                    }
                }
            }
        }
        
    } catch (error) {
        console.error('评估请求错误:', error);
        addEvaluationMessage(`错误: ${error.message}`, 'error');
        hideFunnelIndicator();
    }
}

// 处理评估步骤
function handleEvaluationStep(jsonData) {
    const step = jsonData.step;
    const message = jsonData.message;
    const result = jsonData.result;
    
    switch (step) {
        case 'answering':
            if (result) {
                addEvaluationMessage('回答生成完成：', 'success');
                addEvaluationMessage(result, 'answer');
            } else {
                addEvaluationMessage(message, 'info');
            }
            break;
            
        case 'evaluating':
            if (result) {
                const score = result.score;
                const feedback = result.feedback;
                const issues = result.issues;
                const suggestions = result.suggestions;
                
                addEvaluationMessage(`评估完成（分数: ${score}/100）：`, score >= 85 ? 'success' : 'warning');
                addEvaluationMessage(`反馈: ${feedback}`, 'feedback');
                
                if (issues && issues.length > 0) {
                    addEvaluationMessage(`问题点: ${issues.join(', ')}`, 'error');
                }
                
                if (suggestions && suggestions.length > 0) {
                    addEvaluationMessage(`建议: ${suggestions.join(', ')}`, 'info');
                }
            } else {
                addEvaluationMessage(message, 'info');
            }
            break;
            
        case 're-answering':
            if (result) {
                addEvaluationMessage('重新回答完成：', 'info');
                addEvaluationMessage(result, 'answer');
            } else {
                addEvaluationMessage(message, 'warning');
            }
            break;
            
        case 'accepted':
            addEvaluationMessage(message, 'success');
            break;
            
        case 'max-attempts':
            addEvaluationMessage(message, 'warning');
            break;
            
        case 'following-up':
            if (result) {
                addEvaluationMessage('跟进处理完成：', 'success');
                addEvaluationMessage(result, 'followup');
            } else {
                addEvaluationMessage(message, 'info');
            }
            break;
            
        default:
            addEvaluationMessage(message, 'info');
    }
}

// 添加评估消息
function addEvaluationMessage(message, type) {
    const resultsContent = document.getElementById('results-content');
    if (!resultsContent) return;
    
    const messageElement = document.createElement('div');
    messageElement.classList.add('evaluation-message');
    messageElement.classList.add(`evaluation-${type}`);
    
    // 使用marked.js渲染Markdown
    if (typeof marked !== 'undefined') {
        messageElement.innerHTML = marked.parse(message);
    } else {
        messageElement.textContent = message;
    }
    
    resultsContent.appendChild(messageElement);
    
    // 滚动到底部
    resultsContent.scrollTop = resultsContent.scrollHeight;
}

// 清除评估结果
function clearEvaluationResults() {
    if (confirm('确定要清除所有评估结果吗？')) {
        document.getElementById('user-question').value = '';
        document.getElementById('evaluation-criteria').value = '';
        document.getElementById('follow-up-requirements').value = '';
        
        const evaluationResults = document.getElementById('evaluation-results');
        const resultsContent = document.getElementById('results-content');
        
        if (evaluationResults) {
            evaluationResults.classList.add('hidden');
        }
        if (resultsContent) {
            resultsContent.innerHTML = '';
        }
    }
}


