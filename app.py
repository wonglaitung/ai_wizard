from flask import Flask, request, jsonify, send_from_directory, Response
import sys
import os
import json

# 将llm_services目录添加到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'llm_services'))

# 导入qwen_engine模块
try:
    from llm_services.qwen_engine import chat_with_llm_stream
except ImportError as e:
    print(f"导入qwen_engine时出错: {e}")
    chat_with_llm_stream = None

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('.', 'main.html')

@app.route('/chat')
def chat_page():
    return send_from_directory('.', 'chat.html')



@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

@app.route('/api/chat', methods=['POST'])
def chat():
    if chat_with_llm_stream is None:
        def error_generator():
            yield 'data: ' + json.dumps({'error': '抱歉，AI服务不可用。'}) + '\n\n'
        
        return Response(error_generator(), mimetype='text/event-stream')
    
    try:
        data = request.json
        user_message = data.get('message', '')
        chat_history = data.get('history', [])
        settings = data.get('settings', {})
        output_as_table = data.get('outputAsTable', False)
        
        if not user_message:
            def error_generator():
                yield 'data: ' + json.dumps({'error': '请输入消息。'}) + '\n\n'
            
            return Response(error_generator(), mimetype='text/event-stream')
        
        # 如果需要以表格形式输出，则修改用户消息，添加相关要求
        if output_as_table:
            # 在用户消息中添加要求以表格形式输出的指令
            user_message = f"{user_message}\n\n请以表格的形式组织和呈现您的回答，使用 Markdown 表格格式。"
        
        # 准备传递给模型的参数
        model_params = {
            'model': settings.get('modelName', 'qwen-max'),
            'temperature': settings.get('temperature', 0.7),
            'max_tokens': settings.get('maxTokens', 2048),
            'top_p': settings.get('topP', 0.9),
            'frequency_penalty': settings.get('frequencyPenalty', 0.5),
            'api_key': settings.get('apiKey', None),  # 添加API密钥参数
            'base_url': settings.get('baseUrl', None),  # 添加基础URL参数
            'history': chat_history  # 添加聊天历史记录参数
        }
        
        # 调用Qwen模型获取流式回复
        def generate():
            try:
                for chunk in chat_with_llm_stream(user_message, **model_params):
                    if chunk:
                        yield 'data: ' + json.dumps({'reply': chunk}) + '\n\n'
                # 发送结束信号
                yield 'data: [DONE]\n\n'
            except Exception as e:
                print(f"处理聊天请求时出错: {e}")
                yield 'data: ' + json.dumps({'error': '抱歉，处理您的请求时出错。'}) + '\n\n'
        
        return Response(generate(), mimetype='text/event-stream')
    except Exception as e:
        print(f"处理聊天请求时出错: {e}")
        
        def error_generator():
            yield 'data: ' + json.dumps({'error': '抱歉，处理您的请求时出错。'}) + '\n\n'
        
        return Response(error_generator(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5005)
