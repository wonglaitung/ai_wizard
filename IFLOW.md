# IFLOW 项目文档

## 项目概述

这是一个基于 Flask 的 Web 应用程序，名为"AI数据透视助手"。该应用提供了一个功能丰富的 AI 对话界面，包括可折叠对话框、文件上传分析、图表数据可视化等功能。用户可以通过左侧菜单切换"新对话"和"配置"页面，与 Qwen 大语言模型进行交互。该应用支持流式响应，使 AI 的回复能够逐字显示，并具备强大的数据可视化功能。

应用现在支持智能数据分析功能，用户可以上传数据文件并请求AI进行特定的数据分析任务。系统会自动规划分析任务、处理数据并生成专业的分析报告。此外，应用还具备分步分析能力，可以将复杂的数据分析任务分解为多个步骤执行，包括任务规划、数据处理和报告生成。

## 项目结构

```
/data/ai_wizard/
├── app.py                 # Flask 后端应用
├── main.html              # 前端主页面
├── IFLOW.md               # 项目文档
├── NGINX_DEPLOYMENT.md    # Nginx部署说明
├── README.md              # 项目说明文档
├── requirements.txt       # Python依赖列表
├── set_key.sh             # 设置API密钥的脚本
├── .git/...
├── conf/
│   └── nginx.conf         # Nginx配置文件
├── css/
│   └── styles.css         # 前端样式表
├── docker/
│   └── Dockerfile         # Docker构建文件
├── llm_services/
│   ├── analysis_planner.py # 数据分析任务规划器
│   ├── data_processor.py   # 数据处理模块
│   ├── qwen_engine.py      # Qwen 模型接口
│   └── report_generator.py # 分析报告生成器
└── scripts/
    ├── chart.js           # Chart.js 图表库
    ├── marked.min.js      # Markdown解析库
    └── script.js          # 前端 JavaScript 逻辑
```

## 核心功能

1. **双面板界面**：左侧侧边栏菜单包含"新对话"和"配置"页面，支持收起/展开。
2. **可折叠对话框**：对话框默认收起在右下角，点击机器人图标可展开。
3. **流式 AI 响应**：AI 的回复以流式方式逐字显示，模拟打字机效果。
4. **预设问题**：提供"中国近十年的GDP增长情况"和"展示一个销售数据表格"两个预设问题按钮。
5. **文件上传与分析**：支持上传 txt、csv、xlsx、docx 格式的文件并让 AI 分析内容。
6. **数据可视化**：支持表格数据的图表展示，包括柱状图、折线图、饼图等，并可导出为图片。
7. **AI 模型配置**：提供配置页面，可设置模型参数（模型名称、温度、最大 Token 数、Top P、频率惩罚等）。
8. **Markdown 支持**：对话框和对话区域支持 Markdown 格式渲染。
9. **图表输出模式**：可切换到专门的图表输出模式，支持数据表格的可视化展示。
10. **聊天历史**：支持聊天历史记录和上下文对话。
11. **智能数据分析**：支持上传数据文件并进行智能分析，包括任务规划、数据处理和报告生成。
12. **Token 数量估算**：自动估算上传文件和消息的 token 数量，并在超出限制时给出警告。
13. **分步分析**：将复杂的数据分析任务分解为多个步骤，包括任务规划、数据处理和报告生成。
14. **API 密钥安全**：支持在配置页面安全设置和显示/隐藏API密钥。
15. **多工作表数据处理**：支持处理包含多个工作表的Excel文件。

## 技术栈

- **后端**：Flask (Python)
- **前端**：HTML, CSS, JavaScript
- **AI 模型**：Qwen (通过 API 调用)
- **流式传输**：Server-Sent Events (SSE)
- **数据处理**：pandas, openpyxl, python-docx, numpy
- **图表库**：Chart.js
- **Markdown 解析**：marked.js
- **部署**：Docker, Nginx

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

## Nginx 反向代理配置

项目包含优化的 Nginx 配置文件，用于解决大文件上传和流式传输问题：

- 支持最大 100M 的文件上传
- 优化代理缓冲区设置以支持流式响应
- 针对 API 端点禁用代理缓冲以确保 SSE 正常工作
- 设置适当的超时和缓冲区大小以处理大文件和流响应
- 启用 gzip 压缩以减少传输大小

## 文件说明

### `app.py`

Flask 应用的主文件，负责：

- 提供静态文件服务 (HTML, CSS, JS)
- 处理 `/api/chat` API 请求
- 处理 `/api/config` 配置 API 请求
- 处理 `/api/upload` 文件上传 API 请求
- 调用 Qwen 模型获取流式回复
- 使用 SSE (Server-Sent Events) 实现流式响应
- 实现文件上传处理和格式转换功能
- 添加日志记录功能
- 实现智能数据分析功能，包括分步处理流程
- 实现 token 数量估算和警告功能
- 实现分步分析处理函数，包括任务规划、数据处理和报告生成

### `llm_services/analysis_planner.py`

数据分析任务规划器模块，负责：

- 使用大模型将用户的数据分析请求转换为具体的计算任务
- 生成包含任务类型、列名、操作和预期输出的任务计划
- 提供支持的操作列表和详细说明
- 从业务角度进行数据透视分析
- 包含详细的操作描述，帮助用户理解每个操作的业务用途

### `llm_services/data_processor.py`

数据处理模块，负责：

- 根据任务计划执行具体的数据处理操作
- 支持多种统计计算（平均值、总和、最大值、最小值等）
- 处理多种文件格式的数据
- 包含操作函数注册表和装饰器
- 支持列名模糊匹配和数据清洗
- 支持多工作表数据处理
- 提供30多种数据处理操作函数，涵盖统计、计算、分析等需求

### `llm_services/qwen_engine.py`

Qwen 模型的接口文件，包含：

- `chat_with_llm_stream`：用于获取流式回复的函数
- `chat_with_llm`：用于获取完整回复的函数
- `embed_with_llm`：用于生成文本嵌入的函数
- 支持聊天历史记录、参数验证和错误处理
- 支持自定义 API 基础 URL
- 支持推理模式（enable_thinking）
- 实现参数验证和范围限制
- 支持UTF-8编码处理

### `llm_services/report_generator.py`

分析报告生成器模块，负责：

- 整合计算结果并生成最终分析报告
- 使用大模型生成专业的数据分析报告
- 提供详细的分析报告结构
- 包含对计算结果的解释、关键发现、趋势分析和建议

### `main.html`

前端主页面的结构，包含：

- 左侧侧边栏菜单
- "新对话"页面，包含对话框触发按钮、对话框容器、消息显示区域、输入框和发送按钮、预设问题按钮、文件上传功能
- "配置"页面，包含 API 配置、模型参数设置等
- 图表输出区域
- 支持图表输出切换开关
- 包含必要的脚本引入和初始化代码

### `css/styles.css`

定义了应用的样式，包括：

- 侧边栏菜单的外观和收起/展开动画
- 对话框的外观和位置
- 消息气泡的样式（用户消息和 AI 消息）
- 图表输出区域的样式
- 配置页面的表单样式
- 预设问题按钮的样式
- 可调整大小的容器
- 响应式设计
- 专业图表容器样式
- API 密钥显示/隐藏切换按钮样式
- 专业表格和图表样式
- 图表控制面板样式

### `scripts/script.js`

前端交互逻辑，负责：

- 侧边栏菜单切换和收起功能
- 显示/隐藏对话框
- 处理消息发送和接收
- 处理预设问题
- 与后端 API 交互
- 处理流式响应
- 文件上传和预览功能
- 图表数据解析和渲染
- AI 模型参数配置和本地存储
- 聊天历史记录管理
- 图表类型切换和导出功能
- 智能数据分析的前端交互
- Token 数量估算和警告功能
- 分步分析流程的处理
- API 密钥显示/隐藏功能
- 滑块值实时显示
- 表格数据解析和图表渲染

### `scripts/chart.js`

Chart.js 图表库，用于创建各种数据可视化图表。

### `scripts/marked.min.js`

marked.js Markdown 解析库，用于将 Markdown 格式文本转换为 HTML。

### `conf/nginx.conf`

Nginx配置文件，用于反向代理和优化部署，包含：

- 大文件上传支持配置
- 代理缓冲区优化设置
- 流式响应支持配置
- 超时设置
- Gzip压缩配置
- API端点特殊处理

### `docker/Dockerfile`

Docker构建文件，用于容器化部署，包含：

- Python环境配置
- 系统依赖安装
- Python依赖安装
- 应用代码复制
- 端口暴露和运行命令

### `requirements.txt`

Python依赖列表，包含：

- Flask (2.3.3)
- requests (2.31.0)
- pandas (2.1.4)
- numpy (1.24.3)
- python-docx (0.8.11)
- openpyxl (3.1.2)

### `set_key.sh`

设置API密钥的脚本，用于安全地设置环境变量。

## API 接口

### `/api/chat`

- **方法**：POST
- **内容类型**：application/json
- **请求体**：
  ```json
  {
    "message": "用户输入的消息",
    "file_content": "上传的文件内容（可选）",
    "history": "聊天历史记录（可选）",
    "settings": "AI模型配置参数（可选）",
    "outputAsTable": "是否以表格形式输出（可选，默认false）",
    "stepByStep": "是否使用分步分析（可选，默认false）"
  }
  ```
- **响应**：SSE 流，包含 AI 的回复片段
  ```json
  data: {"reply": "AI回复的片段"}
  ```
- **分步分析响应**：
  ```json
  data: {"step": 1, "message": "正在规划分析任务..."}
  data: {"step": 1, "result": {...}}
  data: {"step": 2, "message": "正在处理数据..."}
  data: {"step": 2, "result": {...}}
  data: {"step": 3, "message": "正在生成分析报告..."}
  data: {"step": 3, "result": "..."}
  ```

### `/api/config`

- **方法**：GET/POST
- **GET 请求体**：无
- **POST 请求体**（设置配置）：
  ```json
  {
    "modelName": "模型名称",
    "baseUrl": "API基础URL",
    "temperature": "温度参数",
    "maxTokens": "最大Token数",
    "topP": "Top P参数",
    "frequencyPenalty": "频率惩罚参数"
  }
  ```
- **响应**：配置信息或操作结果

### `/api/upload`

- **方法**：POST
- **内容类型**：multipart/form-data
- **请求体**：文件上传
- **支持格式**：txt, csv, xlsx, docx
- **响应**：解析后的文件内容

## 开发约定

- 前端代码使用原生 JavaScript，无额外框架
- 后端使用 Flask 提供 RESTful API
- 所有与 Qwen 模型的交互通过 `llm_services/qwen_engine.py` 模块进行
- 流式响应使用 SSE (Server-Sent Events) 实现
- 代码遵循 PEP 8 规范
- 使用本地存储保存用户配置
- 支持多语言（主要中文界面）
- 支持 Markdown 渲染
- 实现了图表数据可视化功能
- 支持文件上传和内容分析
- 实现了智能数据分析功能，包括任务规划、数据处理和报告生成的完整流程
- 实现了 token 数量估算和警告机制
- 使用操作注册器模式管理数据处理操作
- 实现了分步分析处理，将复杂任务分解为多个步骤
- 实现了安全的API密钥管理，优先使用环境变量
- 实现了多工作表Excel文件处理
- 使用日志记录进行调试和错误追踪