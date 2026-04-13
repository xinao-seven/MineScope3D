import { apiClient, isApiError } from './client'

export interface TilesetEntry {
  id: string
  name: string
  url: string
}

/** 获取全部可用 3DTiles 模型入口。 */
export async function fetchTilesets(): Promise<TilesetEntry[]> {
  try {
    const response = await apiClient.get<TilesetEntry[]>('/dashboard/tilesets/')
    return Array.isArray(response.data) ? response.data : []
  } catch (error) {
    const current = await fetchCurrentTileset()
    return current ? [current] : []
  }
}

/** 获取当前可用 3DTiles 模型入口。 */
export async function fetchCurrentTileset(): Promise<TilesetEntry | null> {
  try {
    const response = await apiClient.get<TilesetEntry>('/dashboard/tilesets/current/')
    return response.data
  } catch (error) {
    if (isApiError(error)) {
      console.warn('[MineScope3D] 3DTiles 接口暂不可用。')
    }
    return null
  }
}
