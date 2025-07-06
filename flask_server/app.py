import json
import threading
import time

from flask import Flask, request
from flask_cors import CORS
from flask_sock import Sock

# 创建 Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# 配置 CORS 允许跨域
CORS(app)

# 创建 Sock 实例用于 WebSocket
sock = Sock(app)

# 存储所有连接的 WebSocket 客户端
connected_clients = set()
clients_lock = threading.Lock()


def broadcast_message(message):
    """向所有连接的客户端广播消息"""
    with clients_lock:
        disconnected_clients = set()
        for client in connected_clients:
            try:
                if isinstance(message, dict):
                    client.send(json.dumps(message))
                else:
                    client.send(message)
            except Exception as e:
                print(f"Error sending message to client: {e}")
                disconnected_clients.add(client)

        # 移除断开连接的客户端
        connected_clients.difference_update(disconnected_clients)


@app.route('/')
def index():
    """主页路由"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Flask WebSocket Server</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            #messages { 
                border: 1px solid #ccc; 
                height: 300px; 
                overflow-y: auto; 
                padding: 10px; 
                margin-bottom: 10px; 
                background-color: #f9f9f9;
            }
            #messageInput { 
                width: 70%; 
                padding: 5px; 
                margin-right: 10px; 
            }
            button { 
                padding: 5px 10px; 
                margin-right: 5px; 
            }
            .message { 
                margin: 5px 0; 
                padding: 5px; 
                border-radius: 3px; 
            }
            .system { background-color: #e7f3ff; }
            .user { background-color: #f0f8e7; }
            .server { background-color: #fff3e0; }
        </style>
    </head>
    <body>
        <h1>Flask WebSocket Server (原生 WebSocket)</h1>
        <div id="messages"></div>
        <input type="text" id="messageInput" placeholder="输入消息...">
        <button onclick="sendMessage()">发送消息</button>
        <button onclick="sendCustomEvent()">发送自定义事件</button>
        <button onclick="clearMessages()">清空消息</button>
        
        <script>
            let socket = null;
            const messages = document.getElementById('messages');
            
            // 连接 WebSocket
            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = protocol + '//' + window.location.host + '/ws';
                
                socket = new WebSocket(wsUrl);
                
                socket.onopen = function(event) {
                    console.log('Connected to WebSocket server');
                    addMessage('已连接到 WebSocket 服务器', 'system');
                };
                
                socket.onmessage = function(event) {
                    console.log('Received message:', event.data);
                    try {
                        const data = JSON.parse(event.data);
                        if (data.type === 'custom_event') {
                            addMessage('自定义事件: ' + JSON.stringify(data.payload), 'server');
                        } else {
                            addMessage('收到: ' + (data.message || event.data), 'server');
                        }
                    } catch (e) {
                        addMessage('收到: ' + event.data, 'server');
                    }
                };
                
                socket.onclose = function(event) {
                    console.log('WebSocket connection closed');
                    addMessage('WebSocket 连接已关闭', 'system');
                    // 尝试重新连接
                    setTimeout(connectWebSocket, 3000);
                };
                
                socket.onerror = function(error) {
                    console.error('WebSocket error:', error);
                    addMessage('WebSocket 错误: ' + error, 'system');
                };
            }
            
            function addMessage(message, type = 'user') {
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message ' + type;
                messageDiv.textContent = new Date().toLocaleTimeString() + ' - ' + message;
                messages.appendChild(messageDiv);
                messages.scrollTop = messages.scrollHeight;
            }
            
            function sendMessage() {
                const input = document.getElementById('messageInput');
                if (input.value && socket && socket.readyState === WebSocket.OPEN) {
                    const message = {
                        type: 'message',
                        payload: input.value
                    };
                    socket.send(JSON.stringify(message));
                    addMessage('发送: ' + input.value, 'user');
                    input.value = '';
                } else {
                    addMessage('WebSocket 未连接或消息为空', 'system');
                }
            }
            
            function sendCustomEvent() {
                if (socket && socket.readyState === WebSocket.OPEN) {
                    const customData = {
                        type: 'custom_event',
                        payload: {
                            timestamp: new Date().toISOString(),
                            data: 'Hello from client!',
                            random: Math.random()
                        }
                    };
                    socket.send(JSON.stringify(customData));
                    addMessage('发送自定义事件: ' + JSON.stringify(customData.payload), 'user');
                } else {
                    addMessage('WebSocket 未连接', 'system');
                }
            }
            
            function clearMessages() {
                messages.innerHTML = '';
            }
            
            // 监听 Enter 键
            document.getElementById('messageInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
            
            // 页面加载时连接 WebSocket
            window.addEventListener('load', connectWebSocket);
        </script>
    </body>
    </html>
    '''


@sock.route('/ws')
def websocket_handler(ws):
    """WebSocket 连接处理器"""
    print('Client connected to WebSocket')

    # 添加客户端到连接列表
    with clients_lock:
        connected_clients.add(ws)

    try:
        # 发送欢迎消息
        welcome_message = {
            'type': 'message',
            'payload': '欢迎连接到 WebSocket 服务器！'
        }
        ws.send(json.dumps(welcome_message))

        # 持续监听消息
        while True:
            try:
                message = ws.receive()
                if message:
                    print(f'Received message: {message}')

                    try:
                        data = json.loads(message)
                        msg_type = data.get('type', '')
                        payload = data.get('payload', message)

                        if msg_type == 'agentRequest':
                            # 处理普通消息
                            response = {
                                'type': 'agentRequest',
                                'payload': f'服务器回复: {payload}'
                            }
                            broadcast_message(response)

                        elif msg_type == 'wpsRequest':
                            # 处理自定义事件
                            response = {
                                'type': 'custom_event',
                                'payload': {
                                    'response': f'已处理自定义事件',
                                    'original_data': payload,
                                    'server_timestamp': time.time()
                                }
                            }
                            broadcast_message(response)

                    except json.JSONDecodeError:
                        # 如果不是 JSON 格式，当作普通文本处理
                        response = {
                            'type': 'message',
                            'payload': f'服务器回复: {message}'
                        }
                        broadcast_message(response)

            except Exception as e:
                print(f'Error receiving message: {e}')
                break

    except Exception as e:
        print(f'WebSocket error: {e}')
    finally:
        # 从连接列表中移除客户端
        with clients_lock:
            connected_clients.discard(ws)
        print('Client disconnected from WebSocket')


@app.route('/health')
def health_check():
    """健康检查接口"""
    return {
        'status': 'healthy',
        'message': 'Flask WebSocket server is running',
        'connected_clients': len(connected_clients)
    }


@app.route('/stats')
def stats():
    """统计信息接口"""
    return {
        'connected_clients': len(connected_clients),
        'server_time': time.time()
    }


if __name__ == '__main__':
    print("Starting Flask WebSocket server...")
    print("Server will be available at: http://localhost:5000")
    print("WebSocket endpoint: ws://localhost:5000/ws")
    app.run(debug=True, host='0.0.0.0', port=5000)
