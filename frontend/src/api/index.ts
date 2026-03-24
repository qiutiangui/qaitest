/**
 * API请求封装
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 90000,  // 增加到90秒，因为测试用例生成需要时间
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default api
