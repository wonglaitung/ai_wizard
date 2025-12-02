from flask import Flask, request, jsonify, send_from_directory, Response
import sys
import os
import json
import tempfile
import logging
import os

# 从环境变量获取日志级别，默认为INFO
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
numeric_level = getattr(logging, log_level, logging.INFO)

# 配置日志
logging.basicConfig(
    level=numeric_level,
    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s'
)

# 将llm_services目录添加到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'llm_services'))

# 导入LangGraph和相关模块
try:
    from langgraph_services.analysis_graph import AnalysisState, ChatState, get_analysis_graph, get_chat_graph, get_conditional_graph
    from llm_services.qwen_engine import chat_with_llm_stream
    from llm_services.chat_history_compressor import compress_chat_history, estimate_token_count
    from llm_services.data_processor import _convert_pandas_types
    # 获取图实例
    analysis_graph = get_analysis_graph()
    chat_graph = get_chat_graph()
    conditional_graph_executor = get_conditional_graph()
except ImportError as e:
    print(f"导入LangGraph或llm_services模块时出错: {e}")
    analysis_graph = None
    chat_graph = None
    conditional_graph_executor = None
    chat_with_llm_stream = None
    compress_chat_history = None
    _convert_pandas_types = None
    estimate_token_count = None
    
    # 定义一个默认的压缩函数，以防导入失败
    def compress_chat_history(chat_history, max_tokens=8196, keep_recent_ratio=0.7):
        """默认的压缩函数，简单返回原历史记录"""
        print("警告：无法导入压缩函数，返回原始历史记录")
        return chat_history if chat_history else []


app = Flask(__name__)

@app.route('/')
def index():
    app.logger.info('访问根路径 /')
    return send_from_directory('.', 'main.html')

@app.route('/<path:filename>')
def static_files(filename):
    app.logger.info(f'访问静态文件: {filename}')
    try:
        response = send_from_directory('.', filename)
        app.logger.info(f'成功提供文件: {filename}')
        return response
    except Exception as e:
        app.logger.error(f'提供文件 {filename} 时出错: {str(e)}')
        raise

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """处理AI配置的API端点"""
    app.logger.info(f'API配置请求 - 方法: {request.method}, 路径: {request.path}')
    
    if request.method == 'GET':
        # 返回当前配置信息（不包括敏感信息如API密钥）
        config_data = {
            'modelName': os.getenv('QWEN_MODEL_NAME', 'qwen-max'),
            'baseUrl': os.getenv('QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
            'temperature': float(os.getenv('QWEN_TEMPERATURE', '0.7')),
            'maxTokens': int(os.getenv('QWEN_MAX_TOKENS', '8196')),
            'topP': float(os.getenv('QWEN_TOP_P', '0.9')),
            'frequencyPenalty': float(os.getenv('QWEN_FREQUENCY_PENALTY', '0.5'))
        }
        app.logger.debug(f'返回配置数据: {config_data}')
        return jsonify(config_data)
    
    elif request.method == 'POST':
        # 保存配置信息
        try:
            data = request.json
            app.logger.debug(f'接收到的配置数据: {data}')
            
            # 只更新提供的配置项
            if 'modelName' in data:
                os.environ['QWEN_MODEL_NAME'] = str(data['modelName'])
            if 'baseUrl' in data:
                os.environ['QWEN_BASE_URL'] = str(data['baseUrl'])
            if 'temperature' in data:
                os.environ['QWEN_TEMPERATURE'] = str(data['temperature'])
            if 'maxTokens' in data:
                os.environ['QWEN_MAX_TOKENS'] = str(data['maxTokens'])
            if 'topP' in data:
                os.environ['QWEN_TOP_P'] = str(data['topP'])
            if 'frequencyPenalty' in data:
                os.environ['QWEN_FREQUENCY_PENALTY'] = str(data['frequencyPenalty'])
            
            # 注意：API密钥不通过此接口保存到环境变量，以提高安全性
            # 应通过环境变量或安全的配置文件设置
            app.logger.info('配置保存成功')
            return jsonify({'status': 'success', 'message': '配置已保存'})
        except Exception as e:
            app.logger.error(f'保存配置时出错: {str(e)}')
            return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    app.logger.info('收到聊天API请求')
    app.logger.debug(f'请求头: {dict(request.headers)}')
    
    if get_conditional_graph() is None:
        app.logger.error('conditional_graph_executor 未定义，LangGraph服务不可用')
        def error_generator():
            app.logger.debug('生成LangGraph服务不可用错误消息')
            yield 'data: ' + json.dumps({'error': '抱歉，LangGraph服务不可用。'}) + '\n\n'
        
        return Response(error_generator(), mimetype='text/event-stream')
    
    try:
        data = request.json
        app.logger.debug(f'接收到聊天数据: {data}')
        
        user_message = data.get('message', '')
        original_file_content = data.get('file_content', '')  # 获取上传的原始文件内容
        chat_history = data.get('history', [])
        settings = data.get('settings', {})
        output_as_table = data.get('outputAsTable', False)
        step_by_step = data.get('stepByStep', False)  # 是否使用分步分析
        
        # 检查文件内容是否过大，避免超出大模型的上下文限制
        file_content_preview = original_file_content
        if original_file_content and estimate_token_count:
            # 获取配置的maxTokens并计算安全阈值（70%）
            max_tokens = settings.get('maxTokens', 8196)
            safe_threshold = int(max_tokens * 0.7)
            
            # 估算文件内容的token数量
            file_token_count = estimate_token_count(original_file_content)
            
            # 如果文件内容超过安全阈值，则进行截断
            if file_token_count > safe_threshold:
                # 记录截断操作
                app.logger.info(f'文件内容过大 ({file_token_count} tokens)，已截断用于大模型对话，完整内容用于数据处理')
                
                # 根据估算的token数量计算应保留的字符数，使用简单比例计算
                # 因为estimate_token_count使用的是字符级估算，我们可以反向计算
                total_chars = len(original_file_content)
                # 估算平均每个字符对应的token数
                avg_token_per_char = file_token_count / total_chars if total_chars > 0 else 0.25
                # 计算应该保留的字符数
                chars_to_keep = int(safe_threshold / avg_token_per_char) if avg_token_per_char > 0 else safe_threshold
                
                # 截取前chars_to_keep个字符作为预览内容
                file_content_preview = original_file_content[:chars_to_keep]
                app.logger.debug(f'文件内容已从 {total_chars} 字符截断为 {chars_to_keep} 字符用于大模型')

        # 输入验证
        if not user_message and not file_content_preview:
            def error_generator():
                yield 'data: ' + json.dumps({'error': '消息内容不能为空。'}) + '\n\n'
            return Response(error_generator(), mimetype='text/event-stream')
        
        # 压缩历史记录以避免超出token限制
        if compress_chat_history:
            compressed_chat_history = compress_chat_history(chat_history, settings.get('maxTokens', 8196), 0.7, settings)
        else:
            compressed_chat_history = chat_history  # 如果函数不可用，使用原始历史记录
        
        # 准备初始状态
        initial_state: AnalysisState = {
            "user_message": user_message,
            "file_content": file_content_preview,  # 使用截断的预览内容
            "original_file_content": original_file_content,  # 保存完整的原始文件内容用于数据处理
            "chat_history": compressed_chat_history,
            "settings": settings,
            "output_as_table": output_as_table,
            "task_plan": None,
            "computation_results": None,
            "final_report": None,
            "current_step": "initial",
            "error": None,
            "api_key": settings.get('apiKey') or os.getenv('QWEN_API_KEY'),
            "processed": False,
            "iteration_count": 0,
            "max_iterations": 5,  # 设置最大迭代次数
            "observation": None,
            "needs_replanning": False,
            "plan_history": []
        }
        
        # 使用条件图执行器来决定使用哪个流程
        return run_conditional_graph(initial_state)
    except ValueError as ve:
        # 处理请求数据验证错误
        app.logger.error(f"请求数据验证错误: {ve}")
        def error_generator():
            yield 'data: ' + json.dumps({'error': f'请求数据格式错误：{str(ve)}'}) + '\n\n'
        return Response(error_generator(), mimetype='text/event-stream')
    except Exception as e:
        app.logger.error(f"处理聊天请求时出错: {e}")
        
        def error_generator():
            try:
                yield 'data: ' + json.dumps({'error': f'抱歉，处理您的请求时出错：{str(e)}'}) + '\n\n'
            except Exception as inner_e:
                app.logger.error(f"生成错误响应时出错: {inner_e}")
                yield 'data: ' + json.dumps({'error': '抱歉，处理您的请求时发生未知错误。'}) + '\n\n'
        
        return Response(error_generator(), mimetype='text/event-stream')


def run_conditional_graph(initial_state: AnalysisState):
    """
    使用条件图执行器运行适当的流程
    
    Args:
        initial_state (AnalysisState): 初始状态
        
    Returns:
        Response: 流式响应
    """
    app.logger.info('开始LangGraph条件路由处理')
    
    # 检查是否需要分步分析
    needs_step_by_step = (
        initial_state.get("file_content") and initial_state["file_content"] != '' or
        any(keyword in initial_state["user_message"].lower() for keyword in 
            ['分析', '统计', '计算', '数据透视', '报表', '趋势', '对比', '步骤', 'step by step'])
    )
    
    if needs_step_by_step:
        # 对于分步分析，使用分析图并流式输出中间结果
        return run_analysis_with_streaming(initial_state)
    else:
        # 对于普通聊天，使用聊天图
        return run_chat_with_streaming(initial_state)


def run_analysis_with_streaming(initial_state: AnalysisState):
    """
    使用分析图并流式输出中间结果
    
    Args:
        initial_state (AnalysisState): 初始状态
        
    Returns:
        Response: 流式响应
    """
    app.logger.info('开始LangGraph动态规划分析流程（流式输出）')
    
    def generate():
        try:
            # 直接使用LangGraph的流API来获取中间结果，让LangGraph内部逻辑处理迭代和终止
            current_analysis_graph = get_analysis_graph()
            current_state = initial_state.copy()
            
            for output in current_analysis_graph.stream(current_state):
                # 输出是一个字典，键是节点名称，值是该节点的输出状态
                for node_name, state in output.items():
                    app.logger.info(f'节点 {node_name} 完成，状态: {state.get("current_step", "unknown")}')
                    
                    # 更新当前状态
                    current_state = state
                    
                    # 根据节点类型发送适当的响应
                    if node_name == "plan_analysis" or node_name == "replan_analysis":
                        task_plan = state.get("task_plan")
                        if task_plan:
                            plan_type = "重新规划" if node_name == "replan_analysis" else "初始规划"
                            iteration = state.get("iteration_count", 0) + 1
                            yield 'data: ' + json.dumps({
                                'step': 1, 
                                'message': f'{plan_type}完成，迭代 {iteration}',
                                'result': task_plan.model_dump() if hasattr(task_plan, 'model_dump') else (task_plan.dict() if hasattr(task_plan, 'dict') else task_plan)
                            }) + '\n\n'
                            yield 'data: ' + json.dumps({'step': 2, 'message': f'第 {iteration} 轮处理数据...'}) + '\n\n'
                    elif node_name == "process_data":
                        computation_results = state.get("computation_results")
                        if computation_results:
                            # 使用数据处理器中的序列化函数来确保所有pandas对象都被转换为可序列化的格式
                            safe_results = _convert_pandas_types(computation_results) if _convert_pandas_types else computation_results
                            iteration = state.get("iteration_count", 0) + 1
                            yield 'data: ' + json.dumps({
                                'step': 2, 
                                'message': f'第 {iteration} 轮数据处理完成',
                                'result': safe_results
                            }) + '\n\n'
                    elif node_name == "observe_and_evaluate":
                        observation = state.get("observation")
                        if observation:
                            needs_replanning = state.get("needs_replanning", False)
                            iteration = state.get("iteration_count", 0) + 1
                            
                            yield 'data: ' + json.dumps({
                                'step': 3,
                                'message': f'第 {iteration} 轮评估完成，质量评分: {observation.quality_score:.2f}',
                                'result': {
                                    'quality_score': observation.quality_score,
                                    'feedback': observation.feedback,
                                    'success': observation.success,
                                    'next_actions': observation.next_actions,
                                    'needs_replanning': needs_replanning
                                }
                            }) + '\n\n'
                            
                            # 如果质量评分达到阈值且不需要重规划，则表示流程即将结束
                            quality_threshold = float(os.getenv('QUALITY_THRESHOLD', 0.85))
                            if observation.quality_score >= quality_threshold and not needs_replanning:
                                app.logger.info(f'质量评分 {observation.quality_score} >= {quality_threshold}，满足要求，即将生成报告')
                                yield 'data: ' + json.dumps({
                                    'step': 3,
                                    'message': f'质量评分 {observation.quality_score:.2f} 满足要求，提前终止迭代，准备生成报告',
                                    'result': {
                                        'quality_score': observation.quality_score,
                                        'feedback': observation.feedback,
                                        'success': observation.success,
                                        'next_actions': observation.next_actions,
                                        'needs_replanning': needs_replanning
                                    }
                                }) + '\n\n'
                    elif node_name == "generate_report":
                        final_report = state.get("final_report")
                        if final_report:
                            # 确保报告内容中的特殊字符被正确转义
                            if isinstance(final_report, str):
                                # 使用json.dumps处理字符串内容，确保正确转义
                                safe_report = json.dumps(final_report, ensure_ascii=False)
                                iteration = state.get("iteration_count", 0) + 1
                                yield 'data: ' + json.dumps({
                                    'step': 4,
                                    'message': f'生成最终报告，迭代 {iteration} 完成',
                                    'result': json.loads(safe_report)
                                }) + '\n\n'
                            else:
                                iteration = state.get("iteration_count", 0) + 1
                                yield 'data: ' + json.dumps({
                                    'step': 4,
                                    'message': f'生成最终报告，迭代 {iteration} 完成',
                                    'result': final_report
                                }) + '\n\n'
        
            # 发送结束信号
            app.logger.info('LangGraph动态规划分析流程完成')
            yield 'data: [DONE]\n\n'
        except Exception as e:
            app.logger.error(f"LangGraph动态规划分析流程处理时出错: {e}")
            yield 'data: ' + json.dumps({'error': f'LangGraph动态规划分析流程处理时出错：{str(e)}'}) + '\n\n'
    
    return Response(generate(), mimetype='text/event-stream')


def run_chat_with_streaming(initial_state: AnalysisState):
    """
    使用聊天图并流式输出结果
    对于真正流式的聊天响应，我们需要直接使用LLM的流式API
    
    Args:
        initial_state (AnalysisState): 初始状态
        
    Returns:
        Response: 流式响应
    """
    app.logger.info('开始LangGraph聊天流程（流式输出）')
    
    def generate():
        try:
            # 直接使用LLM的流式API来实现真正的流式输出
            from llm_services.qwen_engine import chat_with_llm_stream
            
            user_message = initial_state["user_message"]
            file_content = initial_state["file_content"]
            chat_history = initial_state["chat_history"]
            settings = initial_state["settings"]
            output_as_table = initial_state["output_as_table"]  # 获取表格输出设置
            
            # 压缩历史记录以避免超出token限制
            if compress_chat_history:
                compressed_chat_history = compress_chat_history(chat_history, settings.get('maxTokens', 8196), 0.7, settings)
            else:
                compressed_chat_history = chat_history  # 如果函数不可用，使用原始历史记录
            
            # 如果需要表格输出，修改用户消息以包含相关指令
            original_user_message = user_message
            if output_as_table:
                table_instruction = "\n\n请在回答中尽可能使用表格来组织和呈现数据，特别是当涉及数值、比较或分类信息时。使用Markdown表格格式。"
                user_message = original_user_message + table_instruction
            
            # 如果有文件内容，将其添加到用户消息中
            if file_content:
                user_message = f"请分析以下文件内容：\n\n{file_content}\n\n{user_message}"
            
            # 准备模型参数
            from llm_services.qwen_engine import create_model_params
            model_params = create_model_params(
                settings=settings,
                api_key=settings.get('apiKey'),  # 只使用settings中的api_key参数
                default_model='qwen-max',
                default_temperature=0.7,  # 聊天使用用户设置的温度
                default_max_tokens=2048   # 使用用户配置的值，但确保足够大
            )
            
            app.logger.info(f'开始调用LLM流式API，表格输出模式: {output_as_table}')
            
            # 调用模型获取流式回复
            for chunk in chat_with_llm_stream(user_message, **model_params):
                if chunk:
                    yield 'data: ' + json.dumps({'reply': chunk}) + '\n\n'
            
            # 发送结束信号
            app.logger.info('LangGraph聊天流程完成')
            yield 'data: [DONE]\n\n'
        except Exception as e:
            app.logger.error(f"LangGraph聊天流程处理时出错: {e}")
            yield 'data: ' + json.dumps({'error': f'LangGraph聊天流程处理时出错：{str(e)}'}) + '\n\n'
    
    return Response(generate(), mimetype='text/event-stream')




# 支持的文件类型
ALLOWED_EXTENSIONS = {'txt', 'csv', 'xlsx', 'docx'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(filepath, filename):
    """从文件中提取文本内容"""
    file_extension = filename.rsplit('.', 1)[1].lower()
    
    if file_extension == 'txt':
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()
    elif file_extension in ['csv']:
        import pandas as pd
        df = pd.read_csv(filepath)
        # 使用管道符分隔以确保后续处理的一致性
        return df.to_csv(sep='|', index=False)
    elif file_extension in ['xlsx']:
        import pandas as pd
        # 读取所有工作表
        all_sheets = pd.read_excel(filepath, sheet_name=None)
        # 将所有工作表连接成一个字符串，使用管道符分隔以确保后续处理的一致性
        sheet_strings = []
        for sheet_name, df in all_sheets.items():
            sheet_strings.append(f"Sheet: {sheet_name}")
            # 使用管道符分隔以确保后续处理的一致性
            sheet_strings.append(df.to_csv(sep='|', index=False))
            sheet_strings.append("")  # 添加空行分隔
        return "\n".join(sheet_strings)
    elif file_extension == 'docx':
        from docx import Document
        doc = Document(filepath)
        full_text = []
        for paragraph in doc.paragraphs:
            full_text.append(paragraph.text)
        return '\n'.join(full_text)
    else:
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """处理文件上传的API端点"""
    app.logger.info('收到文件上传请求')
    
    try:
        if 'file' not in request.files:
            app.logger.warning('请求中没有文件')
            return jsonify({'error': '没有选择文件'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            app.logger.warning('文件名为空')
            return jsonify({'error': '没有选择文件'}), 400
        
        if file and allowed_file(file.filename):
            app.logger.debug(f'开始处理文件: {file.filename}')
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
                file.save(temp_file.name)
                temp_filename = temp_file.name
                app.logger.debug(f'文件已保存到临时位置: {temp_filename}')
            
            try:
                # 从文件中提取文本内容
                file_content = extract_text_from_file(temp_filename, file.filename)
                app.logger.debug(f'文件内容提取成功，长度: {len(file_content)} 字符')
                
                # 返回文件内容，以便前端可以将其发送给AI
                response_data = {
                    'status': 'success',
                    'message': '文件上传成功',
                    'file_content': file_content,
                    'filename': file.filename
                }
                app.logger.debug(f'返回响应数据: {response_data}')
                return jsonify(response_data)
            finally:
                # 删除临时文件
                os.unlink(temp_filename)
                app.logger.debug(f'临时文件已删除: {temp_filename}')
        else:
            app.logger.warning(f'不支持的文件类型: {file.filename}')
            return jsonify({'error': '不支持的文件类型'}), 400
    except Exception as e:
        app.logger.error(f"处理文件上传时出错: {e}")
        return jsonify({'error': f'处理文件上传时出错: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)
