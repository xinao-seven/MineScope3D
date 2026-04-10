import {
  ImageryLayer,
  Rectangle,
  SingleTileImageryProvider,
  TileMapServiceImageryProvider,
  UrlTemplateImageryProvider,
  Viewer,
} from 'cesium'
import { fromArrayBuffer as openGeoTiffFromBuffer } from 'geotiff'

type SingleTileOptions = Parameters<typeof SingleTileImageryProvider.fromUrl>[1]
type TmsOptions = Parameters<typeof TileMapServiceImageryProvider.fromUrl>[1]

export interface DegreeRectangle {
  west: number
  south: number
  east: number
  north: number
}

export interface UrlTemplateOptions {
  minimumLevel?: number
  maximumLevel?: number
  subdomains?: string[]
}

export class ImageryLayerLoader {
  private readonly viewer: Viewer

  /** 创建影像图层加载器。 */
  constructor(viewer: Viewer) {
    this.viewer = viewer
  }

  /** 将经纬度范围转换为 Cesium 矩形。 */
  static fromDegreeRectangle(bounds: DegreeRectangle): Rectangle {
    return Rectangle.fromDegrees(bounds.west, bounds.south, bounds.east, bounds.north)
  }

  /** 加载单张影像并作为 ImageryLayer 添加到场景。 */
  async addSingleTile(
    imageUrl: string,
    bounds?: DegreeRectangle,
    options: SingleTileOptions = {},
    alpha = 1,
  ): Promise<ImageryLayer> {
    const rectangle = bounds ? ImageryLayerLoader.fromDegreeRectangle(bounds) : undefined
    const provider = await SingleTileImageryProvider.fromUrl(imageUrl, {
      ...options,
      rectangle,
    })

    const layer = this.viewer.imageryLayers.addImageryProvider(provider)
    layer.alpha = alpha
    return layer
  }

  /** 直接读取 TIFF 并在前端内存解码后叠加为单张影像。 */
  async addGeoTiffSingleTile(
    tiffUrl: string,
    bounds?: DegreeRectangle,
    alpha = 1,
  ): Promise<ImageryLayer> {
    const response = await fetch(tiffUrl)
    if (!response.ok) {
      throw new Error(`TIFF 请求失败: ${response.status} ${response.statusText}`)
    }

    const tiffBuffer = await response.arrayBuffer()
    const tiff = await openGeoTiffFromBuffer(tiffBuffer)
    const image = await tiff.getImage()
    const width = image.getWidth()
    const height = image.getHeight()
    const rgbData = await image.readRGB({ interleave: true })
    const imageData = this.buildImageData(rgbData, width, height)

    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const context = canvas.getContext('2d')
    if (!context) {
      throw new Error('无法创建 TIFF 解码画布上下文')
    }
    context.putImageData(imageData, 0, 0)

    return this.addSingleTile(canvas.toDataURL('image/png'), bounds, {}, alpha)
  }

  /** 基于 URL 模板加载切片影像图层。 */
  addUrlTemplate(url: string, options: UrlTemplateOptions = {}, alpha = 1): ImageryLayer {
    const provider = new UrlTemplateImageryProvider({
      url,
      minimumLevel: options.minimumLevel,
      maximumLevel: options.maximumLevel,
      subdomains: options.subdomains,
    })
    const layer = this.viewer.imageryLayers.addImageryProvider(provider)
    layer.alpha = alpha
    return layer
  }

  /** 加载 TMS 服务影像图层。 */
  async addTileMapService(baseUrl: string, options: TmsOptions = {}, alpha = 1): Promise<ImageryLayer> {
    const provider = await TileMapServiceImageryProvider.fromUrl(baseUrl, options)
    const layer = this.viewer.imageryLayers.addImageryProvider(provider)
    layer.alpha = alpha
    return layer
  }

  /** 移除指定影像图层。 */
  remove(layer: ImageryLayer, destroy = true) {
    return this.viewer.imageryLayers.remove(layer, destroy)
  }

  /** 清空全部影像图层。 */
  removeAll(destroy = true) {
    this.viewer.imageryLayers.removeAll(destroy)
  }

  /** 将 GeoTIFF readRGB 结果转换为可绘制 ImageData。 */
  private buildImageData(rgbData: ArrayLike<number>, width: number, height: number): ImageData {
    const pixelCount = width * height
    const target = new Uint8ClampedArray(pixelCount * 4)

    let maxValue = 0
    for (let index = 0; index < rgbData.length; index += 1) {
      const value = Number(rgbData[index])
      if (value > maxValue) {
        maxValue = value
      }
    }
    const scale = maxValue > 255 ? 255 / maxValue : 1

    for (let pixelIndex = 0; pixelIndex < pixelCount; pixelIndex += 1) {
      const rgbIndex = pixelIndex * 3
      const targetIndex = pixelIndex * 4
      target[targetIndex] = this.toByte(rgbData[rgbIndex], scale)
      target[targetIndex + 1] = this.toByte(rgbData[rgbIndex + 1], scale)
      target[targetIndex + 2] = this.toByte(rgbData[rgbIndex + 2], scale)
      target[targetIndex + 3] = 255
    }

    return new ImageData(target, width, height)
  }

  /** 将任意数值安全转换为 8-bit 颜色通道值。 */
  private toByte(value: number, scale: number): number {
    const normalized = Math.round(Number(value) * scale)
    if (normalized < 0) {
      return 0
    }
    if (normalized > 255) {
      return 255
    }
    return normalized
  }
}
