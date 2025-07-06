# Flask WebSocket Server (原生 WebSocket)

这是一个使用原生 WebSocket 的 Flask 应用，具有跨域支持功能。

## 功能特性

- ✅ 原生 WebSocket 实时通信
- ✅ 跨域支持 (CORS)
- ✅ 消息广播
- ✅ 自定义事件处理
- ✅ 简单的 Web 界面用于测试
- ✅ 自动重连机制
- ✅ 连接统计

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行应用

```bash
python app.py
```

服务器将在 `http://localhost:5000` 启动。

## WebSocket 接口

### 连接端点
- **URL**: `ws://localhost:5000/ws`
- **协议**: 原生 WebSocket

### 消息格式

所有消息都使用 JSON 格式：

```json
{
  "type": "message" | "custom_event",
  "payload": "消息内容或数据对象"
}
```

#### 客户端可发送的消息类型：
- `message`: 发送文本消息
- `custom_event`: 发送自定义事件数据

#### 服务器发送的消息类型：
- `message`: 普通文本消息
- `custom_event`: 自定义事件响应

## 测试方法

### 1. 使用内置 Web 界面
打开浏览器访问 `http://localhost:5000`，可以直接测试 WebSocket 功能。

### 2. 使用 JavaScript 客户端
```javascript
// 连接 WebSocket
const socket = new WebSocket('ws://localhost:5000/ws');

// 连接成功
socket.onopen = function(event) {
    console.log('Connected to WebSocket server');
};

// 接收消息
socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

// 发送普通消息
function sendMessage(text) {
    const message = {
        type: 'message',
        payload: text
    };
    socket.send(JSON.stringify(message));
}

// 发送自定义事件
function sendCustomEvent(data) {
    const message = {
        type: 'custom_event',
        payload: data
    };
    socket.send(JSON.stringify(message));
}

// 连接关闭
socket.onclose = function(event) {
    console.log('WebSocket connection closed');
};

// 错误处理
socket.onerror = function(error) {
    console.error('WebSocket error:', error);
};
```

### 3. 使用 Python 客户端
```python
import asyncio
import websockets
import json

async def client():
    uri = "ws://localhost:5000/ws"
    
    async with websockets.connect(uri) as websocket:
        # 发送消息
        message = {
            "type": "message",
            "payload": "Hello from Python client!"
        }
        await websocket.send(json.dumps(message))
        
        # 发送自定义事件
        custom_event = {
            "type": "custom_event",
            "payload": {
                "action": "greeting",
                "data": "Hello Server!"
            }
        }
        await websocket.send(json.dumps(custom_event))
        
        # 接收消息
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")

# 运行客户端
asyncio.run(client())
```

### 4. 使用 curl 测试 (HTTP 接口)
```bash
# 健康检查
curl http://localhost:5000/health

# 查看连接统计
curl http://localhost:5000/stats
```

## API 端点

### HTTP 接口
- `GET /`: 返回测试页面
- `GET /health`: 健康检查接口，返回服务器状态和连接数
- `GET /stats`: 连接统计信息

### WebSocket 接口
- `WS /ws`: WebSocket 连接端点

### WebSocket 配置
- **跨域**: 通过 Flask-CORS 支持跨域请求
- **端口**: 5000
- **主机**: 0.0.0.0 (允许外部访问)
- **自动重连**: 客户端断开后会自动尝试重连

## 消息处理流程

1. **连接建立**: 客户端连接到 `/ws` 端点
2. **欢迎消息**: 服务器发送欢迎消息
3. **消息交换**: 客户端和服务器可以发送 JSON 格式的消息
4. **广播**: 服务器将消息广播给所有连接的客户端
5. **断开处理**: 自动清理断开的连接

## 与 Socket.IO 的区别

| 特性 | Socket.IO | 原生 WebSocket |
|------|-----------|---------------|
| 协议 | Socket.IO 协议 | 标准 WebSocket |
| 连接 | `socket.io-client` | `WebSocket` API |
| 消息格式 | 事件驱动 | JSON 消息 |
| 兼容性 | 需要专门客户端 | 浏览器原生支持 |
| 传输 | 多种传输方式 | WebSocket 传输 |

## 注意事项

1. **生产环境**: 请修改 `SECRET_KEY` 为安全的密钥
2. **跨域设置**: 根据需要调整 CORS 配置
3. **错误处理**: 应用包含基本的错误处理和重连机制
4. **部署**: 建议使用 Gunicorn 或 uWSGI 部署到生产环境
5. **安全性**: 可以根据需求添加身份验证和权限控制

## 扩展功能

- 房间/频道支持
- 用户身份验证
- 消息持久化
- 速率限制
- 心跳检测 