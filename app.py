from flask import Flask, request, jsonify, send_from_directory, Response
import sys
import os
import json
import tempfile
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s'
)

# 将llm_services目录添加到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'llm_services'))

# 导入LangGraph和相关模块
try:
    from langgraph_services.analysis_graph import AnalysisState, analysis_graph
    from llm_services.qwen_engine import chat_with_llm_stream
except ImportError as e:
    print(f"导入LangGraph或llm_services模块时出错: {e}")
    analysis_graph = None
    chat_with_llm_stream = None

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
    
    if analysis_graph is None:
        app.logger.error('analysis_graph 未定义，LangGraph服务不可用')
        def error_generator():
            app.logger.debug('生成LangGraph服务不可用错误消息')
            yield 'data: ' + json.dumps({'error': '抱歉，LangGraph服务不可用。'}) + '\n\n'
        
        return Response(error_generator(), mimetype='text/event-stream')
    
    try:
        data = request.json
        app.logger.debug(f'接收到聊天数据: {data}')
        
        user_message = data.get('message', '')
        file_content = data.get('file_content', '')  # 获取上传的文件内容
        chat_history = data.get('history', [])
        settings = data.get('settings', {})
        output_as_table = data.get('outputAsTable', False)
        step_by_step = data.get('stepByStep', False)  # 是否使用分步分析
        
        # 准备初始状态
        initial_state: AnalysisState = {
            "user_message": user_message,
            "file_content": file_content,
            "chat_history": chat_history,
            "settings": settings,
            "output_as_table": output_as_table,
            "task_plan": None,
            "computation_results": None,
            "final_report": None,
            "current_step": "initial",
            "error": None,
            "api_key": settings.get('apiKey') or os.getenv('QWEN_API_KEY')
        }
        
        # 如果需要分步分析，使用LangGraph处理
        if step_by_step or file_content:
            return run_langgraph_step_by_step(initial_state)
        else:
            # 对于普通聊天，也使用LangGraph进行处理
            return run_langgraph_chat(initial_state)
    except Exception as e:
        app.logger.error(f"处理聊天请求时出错: {e}")
        
        def error_generator():
            try:
                yield 'data: ' + json.dumps({'error': f'抱歉，处理您的请求时出错：{str(e)}'}) + '\n\n'
            except Exception as inner_e:
                app.logger.error(f"生成错误响应时出错: {inner_e}")
                yield 'data: ' + json.dumps({'error': '抱歉，处理您的请求时发生未知错误。'}) + '\n\n'
        
        return Response(error_generator(), mimetype='text/event-stream')


def run_langgraph_step_by_step(initial_state: AnalysisState):
    """
    使用LangGraph运行分步分析
    
    Args:
        initial_state (AnalysisState): 初始状态
        
    Returns:
        Response: 流式响应
    """
    app.logger.info('开始LangGraph分步分析处理')
    
    def generate():
        try:
            # 逐步执行分析流程并输出中间结果
            from langgraph_services.analysis_graph import plan_analysis_task_node, process_data_node, generate_report_node
            
            # 步骤1: 任务规划
            app.logger.info('开始步骤1: 任务规划')
            yield 'data: ' + json.dumps({'step': 1, 'message': '正在规划分析任务...'}) + '\n\n'
            
            state_after_planning = plan_analysis_task_node(initial_state)
            task_plan = state_after_planning.get("task_plan")
            app.logger.info(f'步骤1完成: 任务规划结果 {task_plan}')
            yield 'data: ' + json.dumps({'step': 1, 'result': task_plan.dict() if task_plan else {}}) + '\n\n'
            
            # 步骤2: 数据处理
            app.logger.info('开始步骤2: 数据处理')
            yield 'data: ' + json.dumps({'step': 2, 'message': '正在处理数据...'}) + '\n\n'
            
            state_after_processing = process_data_node(state_after_planning)
            computation_results = state_after_processing.get("computation_results")
            app.logger.info(f'步骤2完成: 数据处理结果 {computation_results}')
            yield 'data: ' + json.dumps({'step': 2, 'result': computation_results}) + '\n\n'
            
            # 步骤3: 报告生成
            app.logger.info('开始步骤3: 报告生成')
            yield 'data: ' + json.dumps({'step': 3, 'message': '正在生成分析报告...'}) + '\n\n'
            
            final_state = generate_report_node(state_after_processing)
            report = final_state.get("final_report")
            app.logger.info(f'步骤3完成: 报告生成结果 {report[:100] if report else "None"}...')  # 只记录前100个字符以避免日志过长
            # 确保报告内容是有效的JSON字符串
            safe_report = report if report and isinstance(report, str) else "未能生成分析报告"
            yield 'data: ' + json.dumps({'step': 3, 'result': safe_report}) + '\n\n'
            
            # 发送结束信号
            app.logger.info('LangGraph分步分析流程完成')
            yield 'data: [DONE]\n\n'
        except Exception as e:
            app.logger.error(f"LangGraph分步分析处理时出错: {e}")
            yield 'data: ' + json.dumps({'error': f'LangGraph分步分析处理时出错：{str(e)}'}) + '\n\n'
    
    return Response(generate(), mimetype='text/event-stream')


def run_langgraph_chat(initial_state: AnalysisState):
    """
    使用LangGraph运行普通聊天
    
    Args:
        initial_state (AnalysisState): 初始状态
        
    Returns:
        Response: 流式响应
    """
    app.logger.info('开始LangGraph聊天处理')
    
    def generate():
        try:
            # 直接调用聊天节点函数，而不是通过图，以避免并发更新问题
            from langgraph_services.analysis_graph import chat_node
            
            # 运行聊天节点
            final_state = chat_node(initial_state)
            
            error = final_state.get('error')
            if error:
                app.logger.error(f'LangGraph处理出错: {error}')
                yield 'data: ' + json.dumps({'error': error}) + '\n\n'
                return
            
            final_report = final_state.get('final_report')
            if final_report:
                # 发送完整回复
                yield 'data: ' + json.dumps({'reply': final_report}) + '\n\n'
            else:
                yield 'data: ' + json.dumps({'error': '未能生成回复'}) + '\n\n'
            
            # 发送结束信号
            app.logger.info('LangGraph聊天流程完成')
            yield 'data: [DONE]\n\n'
        except Exception as e:
            app.logger.error(f"LangGraph聊天处理时出错: {e}")
            yield 'data: ' + json.dumps({'error': f'LangGraph聊天处理时出错：{str(e)}'}) + '\n\n'
    
    return Response(generate(), mimetype='text/event-stream')

# 支持的文件类型
ALLOWED_EXTENSIONS = {'txt', 'csv', 'xlsx', 'docx'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(filepath, filename):
    """从文件中提取文本内容"""
    import os
    file_extension = filename.rsplit('.', 1)[1].lower()
    
    if file_extension == 'txt':
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()
    elif file_extension in ['csv']:
        import pandas as pd
        df = pd.read_csv(filepath)
        return df.to_string()
    elif file_extension in ['xlsx']:
        import pandas as pd
        # 读取所有工作表
        all_sheets = pd.read_excel(filepath, sheet_name=None)
        # 将所有工作表连接成一个字符串
        sheet_strings = []
        for sheet_name, df in all_sheets.items():
            sheet_strings.append(f"工作表: {sheet_name}")
            sheet_strings.append(df.to_string())
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
