// 获取DOM元素 - 只有在元素存在的情况下才获取
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
const fileUploadInput = document.getElementById('file-upload');
const fileNameSpan = document.getElementById('file-name');
const clearFileBtn = document.getElementById('clear-file');

// 配置页面相关元素
const apiKeyInput = document.getElementById('api-key');
const toggleApiKeyBtn = document.getElementById('toggle-api-key');
const baseUrlInput = document.getElementById('base-url');
const modelNameInput = document.getElementById('model-name');
const temperatureInput = document.getElementById('temperature');
const temperatureValue = document.getElementById('temperature-value');
const maxTokensInput = document.getElementById('max-tokens');
const topPInput = document.getElementById('top-p');
const topPValue = document.getElementById('top-p-value');
const frequencyPenaltyInput = document.getElementById('frequency-penalty');
const frequencyPenaltyValue = document.getElementById('frequency-penalty-value');
const saveConfigBtn = document.getElementById('save-config');
const resetConfigBtn = document.getElementById('reset-config');

// 聊天历史记录
let chatHistory = [];
let uploadedFileContent = ''; // 存储上传的文件内容

// 初始化清除按钮状态
if (clearFileBtn) {
    clearFileBtn.style.display = 'none';
}

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
    
    // 调整图表输出区域的位置
    adjustPageOutputPosition();
});

// 文件上传处理
if (fileUploadInput && fileNameSpan && clearFileBtn) {
    fileUploadInput.addEventListener('change', async (event) => {
        const file = event.target.files[0];
        if (file) {
            fileNameSpan.textContent = `正在上传: ${file.name}`;
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
                    // 保存文件内容
                    uploadedFileContent = result.file_content;
                    fileNameSpan.textContent = file.name; // 上传成功后显示文件名
                } else {
                    console.error(`文件上传失败: ${result.error || '未知错误'}`);
                    uploadedFileContent = '';
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
        fileUploadInput.value = '';
        // 重置文件名显示
        fileNameSpan.textContent = '未选择文件';
        // 清空上传的文件内容
        uploadedFileContent = '';
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
                toggleSidebarBtn.textContent = '◀';
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
outputToggle.addEventListener('change', () => {
    console.log('输出开关状态改变:', outputToggle.checked);
    if (outputToggle.checked) {
        pageOutput.classList.remove('hidden');
        console.log('图表输出区域已显示');
    } else {
        pageOutput.classList.add('hidden');
        console.log('图表输出区域已隐藏');
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
                history: chatHistory,
                settings: settings,
                outputAsTable: shouldOutputAsTable
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
                            // 检查是否包含表格，如果是，尝试绘制图表
                            if (outputToggle.checked && outputAiMessageElement) {
                                checkAndRenderChart(outputAiMessageElement);
                            } else if (aiMessageElement) {
                                checkAndRenderChart(aiMessageElement);
                            }
                            return;
                        }
                        
                        try {
                            const jsonData = JSON.parse(data);
                            
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
                            
                            if (jsonData.reply) {
                                aiReply += jsonData.reply;
                                
                                // 根据开关状态更新相应的消息元素
                                if (outputToggle.checked && outputAiMessageElement) {
                                    if (typeof marked !== 'undefined') {
                                        outputAiMessageElement.innerHTML = marked.parse(aiReply);
                                    } else {
                                        outputAiMessageElement.textContent = aiReply;
                                    }
                                    outputMessages.scrollTop = outputMessages.scrollHeight;
                                } else if (aiMessageElement) {
                                    if (typeof marked !== 'undefined') {
                                        aiMessageElement.innerHTML = marked.parse(aiReply);
                                    } else {
                                        aiMessageElement.textContent = aiReply;
                                    }
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
            chartControls.innerHTML = `
                <label for="chart-type-${index}">图表类型: </label>
                <select id="chart-type-${index}" class="chart-type-selector">
                    <option value="bar">柱状图</option>
                    <option value="line">折线图</option>
                    <option value="pie">饼图</option>
                    <option value="doughnut">环形图</option>
                </select>
            `;
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
            const chartTypeSelector = chartControls.querySelector('.chart-type-selector');
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
    // 为每列创建一个数据集（跳过第一列，假设它是标签）
    for (let col = 1; col < headers.length; col++) {
        const data = [];
        for (let i = 1; i < rows.length; i++) {
            const cell = rows[i].querySelectorAll('th, td')[col];
            if (cell) {
                const value = parseFloat(cell.textContent.trim());
                if (!isNaN(value)) {
                    data.push(value);
                } else {
                    // 如果不是数字，尝试转换
                    data.push(0);
                }
            } else {
                data.push(0);
            }
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
        }
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
        outputIndicator.textContent = '正在输入...';
        outputMessages.appendChild(outputIndicator);
        outputMessages.scrollTop = outputMessages.scrollHeight;
    } else {
        // 如果开关关闭，只在对话框中显示"正在输入"提示
        chatIndicator = document.createElement('div');
        chatIndicator.classList.add('message', 'ai-message');
        chatMessages.appendChild(chatIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    return { chatIndicator: chatIndicator, outputIndicator: outputIndicator };
}

// 配置页面功能
document.addEventListener('DOMContentLoaded', function() {
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
});

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

// 重置配置