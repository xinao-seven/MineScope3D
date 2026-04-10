import axios from 'axios'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 6000,
})

/** 判断当前错误是否来自后端接口调用。 */
export function isApiError(error: unknown): boolean {
  return axios.isAxiosError(error)
}
