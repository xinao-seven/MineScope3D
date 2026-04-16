import {
    Cartesian3,
    Cartographic,
    Color,
    Entity,
    JulianDate,
    Math as CesiumMath,
    PropertyBag,
    type Viewer,
} from 'cesium'
import { EntityManager } from './EntityManager'

export interface AnnotationRecord {
    id: string
    name: string
    position: Cartesian3
}

export interface AnnotationAddResult {
    annotation: AnnotationRecord
    longitude: number
    latitude: number
}

export class AnnotationManager {
    private readonly viewer: Viewer
    private readonly entityManager: EntityManager
    private readonly annotations = new Map<string, AnnotationRecord>()
    private readonly entities = new Map<string, Entity>()
    private selectedId: string | null = null
    private serial = 0

    constructor(viewer: Viewer, entityManager: EntityManager) {
        this.viewer = viewer
        this.entityManager = entityManager
    }

    /** 返回下一个默认标注名。 */
    createDefaultName(): string {
        return `标注 ${this.serial + 1}`
    }

    /** 添加标注并返回经纬度。 */
    addAt(position: Cartesian3, name?: string): AnnotationAddResult {
        this.serial += 1
        const safeName = (name ?? '').trim() || `标注 ${this.serial}`
        const id = `annotation-${Date.now()}-${this.serial}`
        const annotation: AnnotationRecord = {
            id,
            name: safeName,
            position: Cartesian3.clone(position),
        }

        this.annotations.set(id, annotation)
        this.createEntity(annotation)
        this.selectedId = id

        const geo = Cartographic.fromCartesian(position)
        return {
            annotation,
            longitude: CesiumMath.toDegrees(geo.longitude),
            latitude: CesiumMath.toDegrees(geo.latitude),
        }
    }

    /** 重新创建所有标注实体，供场景重绘后恢复。 */
    restoreEntities() {
        this.entities.clear()
        for (const annotation of this.annotations.values()) {
            this.createEntity(annotation)
        }
    }

    /** 判断实体是否为标注实体。 */
    isAnnotationEntity(entity: Entity): boolean {
        return this.readProperty(entity, 'domainType') === 'annotation'
    }

    /** 根据点击实体更新当前选中标注。 */
    selectByEntity(entity: Entity): AnnotationRecord | null {
        if (!this.isAnnotationEntity(entity)) {
            this.selectedId = null
            return null
        }
        const id = this.readProperty(entity, 'targetId')
        return this.selectById(id)
    }

    /** 通过 ID 选中标注。 */
    selectById(id: string): AnnotationRecord | null {
        if (!this.annotations.has(id)) {
            this.selectedId = null
            return null
        }
        this.selectedId = id
        return this.annotations.get(id) ?? null
    }

    /** 清空选中状态。 */
    clearSelection() {
        this.selectedId = null
    }

    /** 获取当前选中标注。 */
    getSelected(): AnnotationRecord | null {
        if (!this.selectedId) {
            return null
        }
        return this.annotations.get(this.selectedId) ?? null
    }

    /** 重命名当前选中标注。 */
    renameSelected(name: string): AnnotationRecord | null {
        const selected = this.getSelected()
        if (!selected) {
            return null
        }
        const safeName = name.trim()
        if (!safeName) {
            return null
        }

        selected.name = safeName
        const entity = this.entities.get(selected.id)
        if (entity) {
            entity.name = safeName
            if (entity.label) {
                ;(entity.label as any).text = safeName
            }
        }
        return selected
    }

    /** 删除当前选中标注。 */
    deleteSelected(): AnnotationRecord | null {
        const selected = this.getSelected()
        if (!selected) {
            return null
        }

        const entity = this.entities.get(selected.id)
        if (entity) {
            this.viewer.entities.remove(entity)
        }
        this.entities.delete(selected.id)
        this.annotations.delete(selected.id)
        this.selectedId = null
        return selected
    }

    /** 清空全部标注。 */
    clearAll() {
        for (const entity of this.entities.values()) {
            this.viewer.entities.remove(entity)
        }
        this.entities.clear()
        this.annotations.clear()
        this.selectedId = null
    }

    private createEntity(annotation: AnnotationRecord) {
        const entity = this.entityManager.addPoint({
            id: annotation.id,
            name: annotation.name,
            position: annotation.position,
            pixelSize: 12,
            color: Color.fromCssColorString('#ff8a3d'),
            outlineColor: Color.fromCssColorString('#2b1308'),
            outlineWidth: 2,
            labelText: annotation.name,
            tag: 'annotation',
        })

        entity.properties = new PropertyBag({
            domainType: 'annotation',
            targetId: annotation.id,
            tag: 'annotation',
        })
        this.entities.set(annotation.id, entity)
    }

    private readProperty(entity: Entity, key: string): string {
        const values = entity.properties?.getValue(JulianDate.now()) as Record<string, unknown> | undefined
        return String(values?.[key] ?? '')
    }
}