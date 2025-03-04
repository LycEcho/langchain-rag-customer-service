from flask import Flask, request, jsonify
import json
from tools_retriever import process_customer_question

app = Flask(__name__)

@app.route('/ask', methods=['POST'])
def ask_question():
    """处理问题请求的API端点"""
    try:
        # 获取请求数据
        data = request.json
        
        # 验证必要参数
        if not data or 'question' not in data:
            return jsonify({'error': '请求中缺少问题参数'}), 400
        
        question = data['question']
        user_id = data.get('user_id', 'default_user')
        chat_history = data.get('chat_history')
        
        # 处理问题
        response = process_customer_question(
            question=question,
            user_id=user_id,
            chat_history=chat_history
        )
        
        return jsonify({
            'question': question,
            'answer': response,
            'user_id': user_id
        })
        
    except Exception as e:
        return jsonify({'error': f'处理请求时出错: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({'status': 'ok', 'message': '服务正常运行'})

if __name__ == '__main__':
    print("启动API服务器，监听端口5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)