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

# 导入qwen_engine模块
try:
    from llm_services.qwen_engine import chat_with_llm_stream
    from llm_services.analysis_planner import plan_analysis_task
    from llm_services.data_processor import process_data
    from llm_services.report_generator import generate_report
except ImportError as e:
    print(f"导入llm_services模块时出错: {e}")
    chat_with_llm_stream = None

app = Flask(__name__)

@app.route('/')
def index():
    app.logger.info('访问根路径 /')
    return send_from_directory('.', 'main.html')

@app.route('/chat')
def chat_page():
    app.logger.info('访问 /chat 路径')
    return send_from_directory('.', 'chat.html')

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
    
    if chat_with_llm_stream is None:
        app.logger.error('chat_with_llm_stream 未定义，AI服务不可用')
        def error_generator():
            app.logger.debug('生成AI服务不可用错误消息')
            yield 'data: ' + json.dumps({'error': '抱歉，AI服务不可用。'}) + '\n\n'
        
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
        
        # 如果需要分步分析，调用分步分析处理函数
        if step_by_step:
            return step_by_step_analysis(user_message, file_content, settings)
        
        # 如果有文件内容，将其添加到用户消息中
        if file_content:
            user_message = f"请分析以下文件内容：\n\n{file_content}\n\n{user_message}"
            app.logger.debug('已将文件内容添加到用户消息中')
        
        if not user_message:
            app.logger.warning('用户消息为空')
            def error_generator():
                yield 'data: ' + json.dumps({'error': '请输入消息。'}) + '\n\n'
            
            return Response(error_generator(), mimetype='text/event-stream')
        
        # 如果需要以表格形式输出，则修改用户消息，添加相关要求
        if output_as_table:
            # 在用户消息中添加要求以表格形式输出的指令
            user_message = f"{user_message}\n\n请以表格的形式组织和呈现您的回答，使用 Markdown 表格格式。"
            app.logger.debug('已添加表格输出要求到用户消息')
        
        # 准备传递给模型的参数
        model_params = {
            'model': settings.get('modelName', 'qwen-max'),
            'temperature': settings.get('temperature', 0.7),
            'max_tokens': settings.get('maxTokens', 8196),
            'top_p': settings.get('topP', 0.9),
            'frequency_penalty': settings.get('frequencyPenalty', 0.5),
            'api_key': settings.get('apiKey') or os.getenv('QWEN_API_KEY'),  # 优先使用环境变量中的API密钥
            'base_url': settings.get('baseUrl', None),  # 添加基础URL参数
            'history': chat_history  # 添加聊天历史记录参数
        }
        
        app.logger.debug(f'准备调用模型，参数: {model_params}')
        
        # 调用Qwen模型获取流式回复
        def generate():
            try:
                app.logger.debug('开始调用chat_with_llm_stream函数')
                for chunk in chat_with_llm_stream(user_message, **model_params):
                    if chunk:
                        yield 'data: ' + json.dumps({'reply': chunk}) + '\n\n'
                # 发送结束信号
                app.logger.debug('发送流式响应结束信号')
                yield 'data: [DONE]\n\n'
            except ValueError as e:
                app.logger.error(f'ValueError: {str(e)}')
                if "未提供API密钥" in str(e):
                    yield 'data: ' + json.dumps({'error': '请在配置页面设置有效的API密钥。'}) + '\n\n'
                else:
                    app.logger.error(f"处理聊天请求时出错: {e}")
                    yield 'data: ' + json.dumps({'error': f'抱歉，处理您的请求时出错：{str(e)}'}) + '\n\n'
            except Exception as e:
                app.logger.error(f"处理聊天请求时出错: {e}")
                # 打印更多错误信息用于调试
                try:
                    if hasattr(e, 'response') and e.response is not None:
                        app.logger.error(f"响应内容: {e.response.text}")
                        # 尝试获取更详细的错误信息
                        try:
                            error_detail = e.response.json()
                            # 如果error_detail包含嵌套的error对象，尝试提取详细信息
                            if 'error' in error_detail and 'message' in error_detail['error']:
                                error_msg = f"{error_detail['error']['message']}"
                            else:
                                error_msg = f"API错误: {str(e)} - {e.response.text}"
                        except:
                            error_msg = f"API错误: {str(e)} - {e.response.text}"
                    else:
                        error_msg = f'抱歉，处理您的请求时出错：{str(e)}'
                except Exception as inner_e:
                    # 防止错误处理本身出错
                    app.logger.error(f"生成错误消息时出错: {inner_e}")
                    error_msg = '抱歉，处理您的请求时发生未知错误。'
                
                yield 'data: ' + json.dumps({'error': error_msg}) + '\n\n'
        
        app.logger.info('开始发送流式响应')
        return Response(generate(), mimetype='text/event-stream')
    except Exception as e:
        app.logger.error(f"处理聊天请求时出错: {e}")
        
        def error_generator():
            try:
                yield 'data: ' + json.dumps({'error': f'抱歉，处理您的请求时出错：{str(e)}'}) + '\n\n'
            except Exception as inner_e:
                app.logger.error(f"生成错误响应时出错: {inner_e}")
                yield 'data: ' + json.dumps({'error': '抱歉，处理您的请求时发生未知错误。'}) + '\n\n'
        
        return Response(error_generator(), mimetype='text/event-stream')


def step_by_step_analysis(user_message, file_content, settings):
    """
    分步分析处理函数
    
    Args:
        user_message (str): 用户消息
        file_content (str): 文件内容
        settings (dict): 设置参数
        
    Returns:
        Response: 流式响应
    """
    app.logger.info('开始分步分析处理')
    
    def generate():
        try:
            app.logger.info('开始步骤1: 任务规划')
            # 步骤1: 任务规划
            yield 'data: ' + json.dumps({'step': 1, 'message': '正在规划分析任务...'}) + '\n\n'
            # 获取API密钥并传递给任务规划函数
            api_key = settings.get('apiKey') or os.getenv('QWEN_API_KEY')
            task_plan = plan_analysis_task(user_message, file_content, api_key)
            app.logger.info(f'步骤1完成: 任务规划结果 {task_plan}')
            yield 'data: ' + json.dumps({'step': 1, 'result': task_plan}) + '\n\n'
            
            app.logger.info('开始步骤2: 数据处理')
            # 步骤2: 数据处理
            yield 'data: ' + json.dumps({'step': 2, 'message': '正在处理数据...'}) + '\n\n'
            computation_results = process_data(task_plan, file_content)
            app.logger.info(f'步骤2完成: 数据处理结果 {computation_results}')
            yield 'data: ' + json.dumps({'step': 2, 'result': computation_results}) + '\n\n'
            
            app.logger.info('开始步骤3: 报告生成')
            # 步骤3: 报告生成
            yield 'data: ' + json.dumps({'step': 3, 'message': '正在生成分析报告...'}) + '\n\n'
            
            # 准备传递给模型的参数
            model_params = {
                'model': settings.get('modelName', 'qwen-max'),
                'temperature': settings.get('temperature', 0.5),
                'max_tokens': settings.get('maxTokens', 8196),
                'top_p': settings.get('topP', 0.9),
                'frequency_penalty': settings.get('frequencyPenalty', 0.5),
                'api_key': settings.get('apiKey') or os.getenv('QWEN_API_KEY'),
                'base_url': settings.get('baseUrl', None)
            }
            
            # 生成报告
            api_key = settings.get('apiKey') or os.getenv('QWEN_API_KEY')
            report = generate_report(task_plan, computation_results, api_key)
            app.logger.info(f'步骤3完成: 报告生成结果 {report[:100]}...')  # 只记录前100个字符以避免日志过长
            yield 'data: ' + json.dumps({'step': 3, 'result': report}) + '\n\n'
            
            # 发送结束信号
            app.logger.info('分步分析流程完成')
            yield 'data: [DONE]\n\n'
        except Exception as e:
            app.logger.error(f"分步分析处理时出错: {e}")
            yield 'data: ' + json.dumps({'error': f'分步分析处理时出错：{str(e)}'}) + '\n\n'
    
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
        df = pd.read_excel(filepath)
        return df.to_string()
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
