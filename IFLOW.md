# IFLOW 项目文档

## 项目概述

这是一个基于 Flask 的 Web 应用程序，提供了一个可折叠的 AI 对话框。用户可以通过点击右下角的机器人图标来打开对话框，并与 Qwen 大语言模型进行交互。该应用支持流式响应，使 AI 的回复能够逐字显示，提供更好的用户体验。

## 项目结构

```
/data/wizard/
├── app.py                 # Flask 后端应用
├── index.html             # 前端 HTML 页面
├── styles.css             # 前端样式表
├── script.js              # 前端 JavaScript 逻辑
├── llm_services/          # LLM 服务模块
│   └── qwen_engine.py     # Qwen 模型接口
└── set_key.sh             # 环境变量设置脚本
```

## 核心功能

1. **可折叠对话框**：对话框默认收起在右下角，点击机器人图标可展开。
2. **流式 AI 响应**：AI 的回复以流式方式逐字显示，模拟打字机效果。
3. **预设问题**：提供"你能做什么"和"你是谁"两个预设问题按钮。
4. **可调整大小**：对话框支持拖拽调整大小。
5. **实时交互**：支持用户输入消息并获取 AI 回复。

## 技术栈

- **后端**：Flask (Python)
- **前端**：HTML, CSS, JavaScript
- **AI 模型**：Qwen (通过 API 调用)
- **流式传输**：Server-Sent Events (SSE)

## 安装与运行

### 依赖安装

```bash
pip install flask requests
```

### 环境变量设置

确保已设置 QWEN API 密钥：

```bash
source set_key.sh
```

### 启动应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 上运行。

## 文件说明

### `app.py`

Flask 应用的主文件，负责：

- 提供静态文件服务 (HTML, CSS, JS)
- 处理 `/api/chat` API 请求
- 调用 Qwen 模型获取流式回复
- 使用 SSE (Server-Sent Events) 实现流式响应

### `llm_services/qwen_engine.py`

Qwen 模型的接口文件，包含：

- `chat_with_llm_stream`：用于获取流式回复的函数
- `chat_with_llm`：用于获取完整回复的函数
- `embed_with_llm`：用于生成文本嵌入的函数

### `index.html`

前端页面的结构，包含：

- 对话框触发按钮 (右下角机器人图标)
- 对话框容器
- 消息显示区域
- 输入框和发送按钮
- 预设问题按钮

### `styles.css`

定义了应用的样式，包括：

- 对话框的外观和位置
- 消息气泡的样式
- 预设问题按钮的样式
- 可调整大小的容器
- 响应式设计

### `script.js`

前端交互逻辑，负责：

- 显示/隐藏对话框
- 处理消息发送
- 显示预设问题
- 与后端 API 交互
- 处理流式响应

## API 接口

### `/api/chat`

- **方法**：POST
- **内容类型**：application/json
- **请求体**：
  ```json
  {
    "message": "用户输入的消息"
  }
  ```
- **响应**：SSE 流，包含 AI 的回复片段
  ```json
  data: {"reply": "AI回复的片段"}
  ```

## 开发约定

- 前端代码使用原生 JavaScript，无额外框架
- 后端使用 Flask 提供 RESTful API
- 所有与 Qwen 模型的交互通过 `llm_services/qwen_engine.py` 模块进行
- 流式响应使用 SSE (Server-Sent Events) 实现
- 代码遵循 PEP 8 规范