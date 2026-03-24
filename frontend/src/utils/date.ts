/**
 * 统一时间格式化工具
 */

/**
 * 格式化时间戳为 YYYY-MM-DD HH:MM:SS 格式
 */
export const formatDateTime = (timestamp: string | null | undefined): string => {
  if (!timestamp) return '-'
  try {
    const date = new Date(timestamp)
    const year = date.getFullYear()
    const month = (date.getMonth() + 1).toString().padStart(2, '0')
    const day = date.getDate().toString().padStart(2, '0')
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    const seconds = date.getSeconds().toString().padStart(2, '0')
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
  } catch {
    return timestamp
  }
}

/**
 * 格式化时间戳为 YYYY-MM-DD 格式（仅日期）
 */
export const formatDate = (timestamp: string | null | undefined): string => {
  if (!timestamp) return '-'
  try {
    const date = new Date(timestamp)
    const year = date.getFullYear()
    const month = (date.getMonth() + 1).toString().padStart(2, '0')
    const day = date.getDate().toString().padStart(2, '0')
    return `${year}-${month}-${day}`
  } catch {
    return timestamp
  }
}

/**
 * 格式化时间戳为 HH:MM:SS 格式（仅时间）
 */
export const formatTime = (timestamp: string | null | undefined): string => {
  if (!timestamp) return ''
  try {
    const date = new Date(timestamp)
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    const seconds = date.getSeconds().toString().padStart(2, '0')
    return `${hours}:${minutes}:${seconds}`
  } catch {
    return timestamp
  }
}
