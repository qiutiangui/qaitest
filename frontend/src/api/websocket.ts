/**
 * WebSocket服务封装
 * 用于实时接收Agent消息和流式输出
 */

// WebSocket消息类型定义
export interface WebSocketMessage {
  type: 'thinking' | 'response' | 'error' | 'complete' | 'streaming' | 'stream_start' | 'stream_end'
  agent: string
  agent_code: string
  content: string
  timestamp: string
  data?: {
    requirement_id?: number
    requirement_name?: string
    progress?: number
    [key: string]: any
  }
}

// WebSocket回调函数定义
export interface WebSocketCallbacks {
  onMessage: (message: WebSocketMessage) => void
  onError: (error: Event) => void
  onClose: () => void
  onOpen?: () => void
}

/**
 * WebSocket服务类
 */
export class WebSocketService {
  private ws: WebSocket | null = null
  private heartbeatInterval: number | null = null
  private reconnectTimeout: number | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 3000 // 3秒后重连
  private taskId: string = ''
  private callbacks: WebSocketCallbacks | null = null
  private isManualClose = false

  /**
   * 获取WebSocket基础URL
   */
  private getBaseURL(): string {
    // 从当前页面URL推断WebSocket地址
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    return `${protocol}//${host}`
  }

  /**
   * 连接WebSocket
   */
  connect(taskId: string, callbacks: WebSocketCallbacks): void {
    this.taskId = taskId
    this.callbacks = callbacks
    this.isManualClose = false
    this.reconnectAttempts = 0

    const baseURL = this.getBaseURL()
    const wsUrl = `${baseURL}/ws/${taskId}`

    try {
      this.ws = new WebSocket(wsUrl)

      // 连接成功
      this.ws.onopen = () => {
        this.reconnectAttempts = 0
        this.startHeartbeat()
        this.callbacks?.onOpen?.()
      }

      // 接收消息
      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          
          // 处理心跳响应
          if (message.type === 'streaming' && message.content === 'pong') {
            return
          }

          this.callbacks?.onMessage(message)
        } catch (error) {
          console.error('[WebSocket] 消息解析失败:', error)
        }
      }

      // 连接错误
      this.ws.onerror = (error) => {
        console.error('[WebSocket] 连接错误:', error)
        this.callbacks?.onError(error)
      }

      // 连接关闭
      this.ws.onclose = (event) => {
        this.stopHeartbeat()

        // 非手动关闭时尝试重连
        if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.attemptReconnect()
        } else {
          this.callbacks?.onClose()
        }
      }
    } catch (error) {
      console.error('[WebSocket] 创建连接失败:', error)
      this.callbacks?.onError(error as Event)
    }
  }

  /**
   * 尝试重连
   */
  private attemptReconnect(): void {
    this.reconnectAttempts++
    this.reconnectTimeout = window.setTimeout(() => {
      this.connect(this.taskId, this.callbacks!)
    }, this.reconnectDelay)
  }

  /**
   * 启动心跳检测
   */
  private startHeartbeat(): void {
    this.stopHeartbeat()

    this.heartbeatInterval = window.setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000) // 30秒发送一次心跳
  }

  /**
   * 停止心跳检测
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }

  /**
   * 发送消息
   */
  send(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    this.isManualClose = true
    this.stopHeartbeat()

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }

    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect')
      this.ws = null
    }

    this.callbacks = null
  }

  /**
   * 获取连接状态
   */
  getReadyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED
  }

  /**
   * 是否已连接
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

// 创建单例实例
let webSocketInstance: WebSocketService | null = null

/**
 * 获取WebSocket实例（单例模式）
 */
export function getWebSocketInstance(): WebSocketService {
  if (!webSocketInstance) {
    webSocketInstance = new WebSocketService()
  }
  return webSocketInstance
}

/**
 * 连接WebSocket（便捷方法）
 */
export function connectWebSocket(
  taskId: string,
  callbacks: WebSocketCallbacks
): WebSocketService {
  const ws = getWebSocketInstance()
  
  // 如果已有连接，先断开
  if (ws.isConnected()) {
    ws.disconnect()
  }

  ws.connect(taskId, callbacks)
  return ws
}

/**
 * 断开WebSocket连接（便捷方法）
 */
export function disconnectWebSocket(): void {
  if (webSocketInstance) {
    webSocketInstance.disconnect()
    webSocketInstance = null
  }
}
