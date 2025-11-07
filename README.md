# AI 对话框

这是一个基于 Flask 的 Web 应用程序，提供了一个可折叠的 AI 对话框。用户可以通过点击右下角的机器人图标来打开对话框，并与 Qwen 大语言模型进行交互。

## 功能特性

- **可折叠对话框**：对话框默认收起在右下角，点击机器人图标可展开。
- **流式 AI 响应**：AI 的回复以流式方式逐字显示，模拟打字机效果。
- **预设问题**：提供"你能做什么"和"你是谁"两个预设问题按钮。
- **配置页面**：支持配置API密钥、基础URL、模型名称等参数。
- **参数调节**：可调节Temperature、Top-P、最大Token数等模型参数。
- **实时交互**：支持用户输入消息并获取 AI 回复。

## 技术栈

- **后端**：Flask (Python)
- **前端**：HTML, CSS, JavaScript
- **AI 模型**：Qwen (通过 API 调用)

## 安装与运行

### 依赖安装

```bash
pip install flask requests
```

### 环境变量设置

确保已设置 QWEN API 密钥：

```bash
export QWEN_API_KEY=sk-xxx
```

### 启动应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 上运行。

## 使用说明

1. 点击左上角菜单按钮，选择"新对话"或"设置"页面。
2. 在"设置"页面中配置API密钥、基础URL等参数，然后点击保存。
3. 在"新对话"页面，点击右下角的机器人图标打开对话框。
4. 在输入框中输入消息，点击发送按钮或按回车键发送。
5. 点击预设问题按钮快速发送常见问题。

## 项目结构

```
.
├── app.py                 # Flask 后端应用
├── main.html              # 前端 HTML 页面
├── styles.css             # 前端样式表
├── script.js              # 前端 JavaScript 逻辑
├── llm_services/          # LLM 服务模块
│   └── qwen_engine.py     # Qwen 模型接口
└── set_key.sh             # 环境变量设置脚本
```
