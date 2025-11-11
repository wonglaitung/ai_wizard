# AI数据透视助手

这是一个基于 Flask 的 Web 应用程序，提供了一个可折叠的 AI 对话框。用户可以通过点击右下角的机器人图标来打开对话框，并与 Qwen 大语言模型进行交互。该应用支持流式响应，使 AI 的回复能够逐字显示，提供更好的用户体验。

## 功能特性

- **可折叠对话框**：对话框默认收起在右下角，点击机器人图标可展开。
- **流式 AI 响应**：AI 的回复以流式方式逐字显示，模拟打字机效果。
- **预设问题**：提供"中国近十年的GDP增长情况"和"展示一个销售数据表格"两个预设问题按钮。
- **文件上传**：支持上传 txt、csv、xlsx、docx 格式的文件，让 AI 分析文件内容。
- **实时交互**：支持用户输入消息并获取 AI 回复。
- **Markdown 支持**：对话框和对话区域支持 Markdown 格式渲染。
- **图表输出**：支持切换到图表输出模式，可视化数据展示。
- **AI 模型配置**：提供配置页面，可设置模型参数（模型名称、温度、最大 Token 数、Top P、频率惩罚等）。
- **可调整大小**：对话框支持拖拽调整大小（在 IFLOW.md 中提到但未在 UI 中明显实现）。

## 技术栈

- **后端**：Flask (Python)
- **前端**：HTML, CSS, JavaScript
- **AI 模型**：Qwen (通过 API 调用)
- **流式传输**：Server-Sent Events (SSE)
- **Markdown 解析**：marked.js
- **图表库**：Chart.js

## 安装与运行

### 依赖安装

```bash
pip install -r requirements.txt
```

### 环境变量设置

确保已设置 QWEN API 密钥：

```bash
export QWEN_API_KEY=your_api_key_here
```

或者在配置页面中直接设置 API 密钥。

### 启动应用

```bash
python app.py
```

应用将在 `http://localhost:5005` 上运行。

## Docker 部署

项目支持通过 Docker 进行部署：

```bash
docker build -t ai-wizard -f docker/Dockerfile .
```

运行容器：

```bash
docker run -p 5005:5005 -e QWEN_API_KEY=your_api_key_here ai-wizard
```

后台运行容器（使用 `-d` 参数）：

```bash
docker run -d -p 5005:5005 -e QWEN_API_KEY=your_api_key_here ai-wizard
```

为容器命名（使用 `--name` 参数）：

```bash
docker run -d --name ai-wizard-app -p 5005:5005 -e QWEN_API_KEY=your_api_key_here ai-wizard
```

访问 `http://localhost:5005` 即可使用应用。

### Docker 容器管理命令

查看运行中的容器：
```bash
docker ps
```

查看所有容器（包括已停止的）：
```bash
docker ps -a
```

查看容器日志：
```bash
docker logs ai-wizard-app
```

停止容器：
```bash
docker stop ai-wizard-app
```

启动已停止的容器：
```bash
docker start ai-wizard-app
```

删除容器：
```bash
docker rm ai-wizard-app
```

## 使用说明

1. 访问 `http://localhost:5005` 打开应用。
2. 点击左侧菜单中的"新对话"或"配置"页面。
3. 在"新对话"页面，点击右下角的机器人图标打开对话框。
4. 在输入框中输入消息，点击发送按钮或按回车键发送。
5. 点击预设问题按钮快速发送常见问题。
6. 点击上传图标选择文件，让 AI 分析文件内容。
7. 使用对话框中的配置开关切换图表输出模式。
8. 在"配置"页面可以设置 AI 模型参数和 API 信息。

## 项目结构

```
.
├── app.py                 # Flask 后端应用
├── main.html              # 前端主页面
├── css/                   # CSS样式文件目录
│   └── styles.css         # 前端样式表
├── docker/                # Docker相关文件目录
│   └── Dockerfile         # Docker构建文件
├── llm_services/          # LLM 服务模块
│   └── qwen_engine.py     # Qwen 模型接口
├── scripts/               # JavaScript文件目录
│   ├── marked.min.js      # Markdown解析库
│   ├── chart.js           # 图表库
│   └── script.js          # 前端 JavaScript 逻辑
├── requirements.txt       # Python依赖列表
└── README.md              # 项目说明文档
```
