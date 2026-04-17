import { Entity, JulianDate } from 'cesium'

/** 从实体 PropertyBag 中读取字符串属性。 */
export function readEntityProperty(entity: Entity, key: string): string {
    const values = entity.properties?.getValue(JulianDate.now()) as Record<string, unknown> | undefined
    return String(values?.[key] ?? '')
}
