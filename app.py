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
    return send_from_directory('.', 'index.html')

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
        
        if not user_message:
            def error_generator():
                yield 'data: ' + json.dumps({'error': '请输入消息。'}) + '\n\n'
            
            return Response(error_generator(), mimetype='text/event-stream')
        
        # 调用Qwen模型获取流式回复
        def generate():
            try:
                for chunk in chat_with_llm_stream(user_message):
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
    app.run(debug=True)