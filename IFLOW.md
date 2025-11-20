# IFLOW 项目文档

## 项目概述

这是一个基于 Flask 的 Web 应用程序，名为"AI数据透视助手"。该应用提供了一个功能丰富的 AI 对话界面，包括可折叠对话框、文件上传分析、图表数据可视化等功能。用户可以通过左侧菜单切换"新对话"和"配置"页面，与 Qwen 大语言模型进行交互。该应用支持流式响应，使 AI 的回复能够逐字显示，并具备强大的数据可视化功能。

应用现在支持智能数据分析功能，用户可以上传数据文件并请求AI进行特定的数据分析任务。系统会自动规划分析任务、处理数据并生成专业的分析报告。此外，应用还具备分步分析能力，可以将复杂的数据分析任务分解为多个步骤执行，包括任务规划、数据处理和报告生成。

项目现在已经重构为使用LangGraph框架，将原有的线性处理流程转换为基于状态机的架构，使系统更加模块化、可扩展和可维护。最新的版本引入了动态规划分析流程，能够迭代优化分析结果，提供更准确的分析报告。

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
├── langgraph_services/
│   └── analysis_graph.py   # LangGraph状态定义和节点实现
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
7. **AI 模型配置**：提供配置页面，可设置模型参数（模型名称、温度、最大 Token 数、Top P、频率惩罚、API基础URL等）。
8. **Markdown 支持**：对话框和对话区域支持 Markdown 格式渲染。
9. **图表输出模式**：可切换到专门的图表输出模式，支持数据表格的可视化展示。
10. **聊天历史**：支持聊天历史记录和上下文对话。
11. **智能数据分析**：支持上传数据文件并进行智能分析，包括任务规划、数据处理和报告生成。
12. **Token 数量估算**：自动估算上传文件和消息的 token 数量，并在超出限制时给出警告。
13. **分步分析**：将复杂的数据分析任务分解为多个步骤，包括任务规划、数据处理和报告生成。
14. **API 密钥安全**：支持在配置页面安全设置和显示/隐藏API密钥。
15. **多工作表数据处理**：支持处理包含多个工作表的Excel文件。
16. **增强数据处理操作**：提供30多种数据处理操作函数，包括均值、总和、最大值、最小值、计数、百分比、标准差、唯一值、中位数、众数、方差、分位数、范围、首行/末行、缺失值统计、相关性分析等。
17. **聊天历史管理**：支持上下文感知的对话历史管理，实现多轮对话。
18. **API基础URL配置**：支持自定义API基础URL，方便切换不同的服务提供商。
19. **滑块参数实时显示**：配置页面的滑块参数（温度、Top P、频率惩罚）实时显示当前值。
20. **文件上传预览与警告**：文件上传时显示预览并提供token数量警告。
21. **LangGraph驱动的分析流程**：使用LangGraph框架实现可扩展的数据分析流程，支持状态管理和错误恢复。
22. **动态规划分析**：引入动态规划机制，能够迭代优化分析结果，根据评估反馈重新规划和执行分析任务。
23. **迭代分析流程**：支持多轮迭代的数据分析，最多可迭代3轮，每次迭代都会优化分析结果。
24. **智能评估反馈**：系统能够评估分析结果的质量，并根据反馈决定是否需要重新规划或继续执行。

## 技术栈

- **后端**：Flask (Python)
- **AI 流程编排**：LangGraph, langchain-core
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
export QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1  # 可选，自定义API基础URL
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

### 环境变量配置（Docker）

在Docker环境中，可以通过环境变量配置更多参数：

```bash
docker run -d -p 5005:5005 \
  -e QWEN_API_KEY=your_api_key_here \
  -e QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1 \
  -e QWEN_MODEL_NAME=qwen-max \
  -e QWEN_TEMPERATURE=0.7 \
  -e QWEN_MAX_TOKENS=8196 \
  -e QWEN_TOP_P=0.9 \
  -e QWEN_FREQUENCY_PENALTY=0.5 \
  ai-wizard
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
- 调用 LangGraph 节点函数获取流式回复
- 使用 SSE (Server-Sent Events) 实现流式响应
- 实现文件上传处理和格式转换功能
- 添加日志记录功能
- 实现智能数据分析功能，包括分步处理流程
- 实现 token 数量估算和警告功能
- 实现分步分析处理函数，包括任务规划、数据处理和报告生成
- 支持聊天历史记录功能
- 支持多工作表Excel文件处理
- 实现API基础URL配置功能
- 添加更详细的错误处理和调试信息
- 集成LangGraph节点函数，实现状态驱动的数据分析流程
- 修复并发更新错误，通过直接调用节点函数而非图调用
- 优化聊天流式输出，直接使用LLM的流式API以实现真正的逐字输出
- 改进分步分析的流式输出，添加中间步骤进度提示
- 增强表格输出功能，当图表输出开关打开时，自动提示大模型使用表格格式展示数据
- 实现动态规划分析流程，支持迭代优化分析结果
- 添加迭代分析的SSE消息处理，包括迭代计数和重新规划机制
- 实现观察和评估机制，根据分析结果质量决定是否继续迭代

### `langgraph_services/analysis_graph.py`

LangGraph状态定义和节点实现模块，负责：

- 定义 `AnalysisState` 状态类型，包含用户消息、文件内容、任务计划、计算结果等
- 实现任务规划节点，将用户请求转换为具体的分析任务
- 实现数据处理节点，根据任务计划执行具体的数据处理操作
- 实现报告生成节点，整合计算结果并生成最终分析报告
- 实现聊天节点，处理普通聊天请求
- 创建分步分析流程图，定义节点间的流转关系
- 实现条件边逻辑，根据用户请求类型选择合适的处理流程
- 提供完整的分析流程执行函数，支持中间结果的获取
- 实现动态规划分析流程，支持迭代优化
- 实现观察和评估节点，评估分析结果质量
- 实现重新规划节点，根据评估反馈重新制定分析计划
- 添加迭代控制逻辑，支持最多3轮迭代优化
- 实现迭代计数和迭代条件判断功能
- 添加质量评分和反馈机制，用于判断是否需要重新规划

### `llm_services/analysis_planner.py`

数据分析任务规划器模块，负责：

- 使用大模型将用户的数据分析请求转换为具体的计算任务
- 生成包含任务类型、列名、操作和预期输出的任务计划
- 提供支持的操作列表和详细说明
- 从业务角度进行数据透视分析
- 包含详细的操作描述，帮助用户理解每个操作的业务用途
- 支持30多种数据处理操作的业务场景描述
- 生成适合动态规划的任务计划，便于后续迭代优化

### `llm_services/data_processor.py`

数据处理模块，负责：

- 根据任务计划执行具体的数据处理操作
- 支持多种统计计算（平均值、总和、最大值、最小值等）
- 处理多种文件格式的数据
- 包含操作函数注册表和装饰器
- 支持列名模糊匹配和数据清洗
- 支持多工作表数据处理
- 提供30多种数据处理操作函数，涵盖统计、计算、分析等需求，包括：
  - 基础统计：mean, sum, max, min, count, std, variance, median, mode
  - 分布分析：quantile_25, quantile_75, range, percentage
  - 数据质量：missing_count, missing_percentage
  - 数据特征：unique, first, last
  - 关联分析：correlation
- 支持工作表名.列名格式的多工作表数据访问
- 实现数据类型自动转换和错误处理

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
- 实现更安全的API密钥管理
- 添加更详细的错误信息返回

### `llm_services/report_generator.py`

分析报告生成器模块，负责：

- 整合计算结果并生成最终分析报告
- 使用大模型生成专业的数据分析报告
- 提供详细的分析报告结构
- 包含对计算结果的解释、关键发现、趋势分析和建议
- 支持表格格式输出模式
- 从业务角度提供数据洞察和行动建议

### `main.html`

前端主页面的结构，包含：

- 左侧侧边栏菜单
- "新对话"页面，包含对话框触发按钮、对话框容器、消息显示区域、输入框和发送按钮、预设问题按钮、文件上传功能
- "配置"页面，包含 API 配置、模型参数设置等
- 图表输出区域
- 支持图表输出切换开关
- 包含必要的脚本引入和初始化代码
- 改进的响应式设计
- 优化的布局和用户体验

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
- 滑块样式优化，支持实时值显示
- 文件上传区域样式改进
- 专业级UI组件设计

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
- 改进的错误处理和用户反馈
- 增强的图表控制功能（类型切换、导出）
- 改进的多工作表数据处理支持
- 优化的用户体验和交互反馈
- 与LangGraph驱动的后端API兼容
- 动态规划分析流程的前端处理
- 迭代分析结果的显示和处理
- 步骤4及最终报告的正确显示
- 对象类型结果的安全解析和显示

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
- 优化的缓冲区设置以支持SSE流
- 安全的头部设置

### `docker/Dockerfile`

Docker构建文件，用于容器化部署，包含：

- Python环境配置
- 系统依赖安装
- Python依赖安装
- 应用代码复制
- 端口暴露和运行命令
- 优化的构建步骤和层缓存

### `requirements.txt`

Python依赖列表，包含：

- Flask (2.3.3)
- requests (2.31.0)
- pandas (2.1.4)
- numpy (1.24.3)
- python-docx (0.8.11)
- openpyxl (3.1.2)
- langgraph (0.0.60)
- langchain-core (0.2,<0.3)
- pydantic (2.5.0)

### `set_key.sh`

设置API密钥的脚本，用于安全地设置环境变量，包含：

- API密钥和其他环境变量的设置
- 邮件配置选项（可选）
- 安全的密钥管理建议

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
- **动态规划分析响应**：
  ```json
  data: {"step": 1, "message": "第 1 轮规划分析任务..."}
  data: {"step": 2, "message": "第 1 轮处理数据..."}
  data: {"step": 3, "message": "第 1 轮评估完成，质量评分: 0.75"}
  data: {"step": 4, "message": "需要重新规划，开始第 2 轮迭代..."}
  data: {"step": 1, "message": "重新规划完成，迭代 2"}
  data: {"step": 4, "message": "生成最终报告，迭代 2 完成"}
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

## LangGraph 架构说明

### 状态定义

`AnalysisState` 是LangGraph工作流的核心数据结构，包含以下字段：

- `user_message`: 用户输入的消息
- `file_content`: 上传的文件内容
- `chat_history`: 聊天历史记录
- `settings`: AI模型配置参数
- `output_as_table`: 是否以表格形式输出
- `task_plan`: 任务规划结果
- `computation_results`: 数据处理结果
- `final_report`: 最终报告
- `current_step`: 当前处理步骤
- `error`: 错误信息
- `api_key`: API密钥
- `processed`: 标记是否已处理
- `iteration_count`: 迭代次数
- `max_iterations`: 最大迭代次数
- `observation`: 观察结果
- `needs_replanning`: 是否需要重新规划
- `plan_history`: 历史计划

### 节点功能

1. **任务规划节点** (`plan_analysis_task_node`): 将用户的数据分析请求转换为具体的计算任务
2. **数据处理节点** (`process_data_node`): 根据任务计划执行具体的数据处理操作
3. **报告生成节点** (`generate_report_node`): 整合计算结果并生成最终分析报告
4. **聊天节点** (`chat_node`): 处理普通聊天请求
5. **重新规划节点** (`replan_analysis_task_node`): 基于观察结果重新规划分析任务
6. **观察和评估节点** (`observe_and_evaluate_node`): 评估分析结果质量并决定是否需要重新规划

### 条件边逻辑

系统根据用户请求的类型决定使用分步分析流程还是普通聊天流程：

- 当用户上传文件或请求中包含数据分析相关关键词时，使用分步分析流程
- 其他情况下使用普通聊天流程

### 动态规划流程

系统支持动态规划分析流程，包含以下特点：

- 最多支持3轮迭代优化
- 每轮迭代包含：规划 → 处理 → 评估 → (可选)重新规划
- 根据评估结果的质量评分决定是否继续迭代
- 观察和评估节点根据结果质量、反馈和建议的下一步操作来决定是否需要重新规划

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
- 实现了聊天历史记录功能，支持上下文对话
- 提供了更丰富的数据处理操作和业务场景描述
- 支持自定义API基础URL配置
- 实现了滑块参数的实时值显示
- 改进了错误处理和用户反馈机制
- 遵循安全最佳实践，避免在代码中硬编码敏感信息
- 使用LangGraph框架实现可扩展的数据分析流程
- 实现了状态驱动的处理逻辑，支持错误恢复和中间结果获取
- 实现了动态规划机制，支持迭代优化分析结果
- 实现了观察和评估机制，根据结果质量反馈调整分析策略
- 模块化设计，各组件职责明确且可独立测试
- 前端安全处理后端返回的对象类型数据，防止marked.js解析错误
- 正确处理步骤4及最终报告的显示逻辑