import { Color, Entity, PropertyBag, Rectangle } from 'cesium'
import type { BoundaryRegion, Borehole, RasterLayer } from '../../types/dashboard'
import type { EntityManager } from '../managers/EntityManager'
import { degreesArrayToCartesianArray } from './coordinateTransform'

const BOREHOLE_POINT_COLOR = Color.fromCssColorString('#f2c94c')
const BOREHOLE_POINT_OUTLINE_COLOR = Color.fromCssColorString('#04110e')
const MINE_BOUNDARY_COLOR = Color.fromCssColorString('#23d18b')
const WORKFACE_BOUNDARY_COLOR = Color.fromCssColorString('#56ccf2')
const DEFAULT_BOREHOLE_LAYER_COLOR = '#23d18b'

const BOREHOLE_VERTICAL_EXAGGERATION = 4.5
const BOREHOLE_MIN_VISUAL_LENGTH = 10
const BOREHOLE_VISUAL_RADIUS = 5.2

function hasSpatialPosition(borehole: Borehole): boolean {
    return borehole.longitude !== 0 || borehole.latitude !== 0
}

function pickBoundaryColor(boundaryType: BoundaryRegion['type']): Color {
    if (boundaryType === 'mine') {
        return MINE_BOUNDARY_COLOR
    }
    return WORKFACE_BOUNDARY_COLOR
}

/** 添加钻孔点实体并写入目标映射。 */
export function addBoreholePointEntities(
    entityManager: EntityManager,
    boreholes: Borehole[],
    targetMap: Map<string, Entity>,
): void {
    for (const borehole of boreholes) {
        if (!hasSpatialPosition(borehole)) {
            continue
        }

        const entity = entityManager.addPoint({
            id: `borehole-${borehole.id}`,
            name: borehole.name,
            position: { lon: borehole.longitude, lat: borehole.latitude, height: borehole.elevation },
            pixelSize: 13,
            color: BOREHOLE_POINT_COLOR,
            outlineColor: BOREHOLE_POINT_OUTLINE_COLOR,
            outlineWidth: 3,
            labelText: borehole.borehole_code,
            tag: 'borehole',
        })

        entity.properties = new PropertyBag({
            domainType: 'borehole',
            targetId: borehole.id,
            tag: 'borehole',
        })
        targetMap.set(borehole.id, entity)
    }
}

/** 添加钻孔分层圆柱实体并写入目标映射。 */
export function addBoreholeLayerEntities(
    entityManager: EntityManager,
    boreholes: Borehole[],
    targetMap: Map<string, Entity[]>,
): void {
    for (const borehole of boreholes) {
        if (!hasSpatialPosition(borehole) || borehole.layers.length === 0) {
            continue
        }

        const layerEntities: Entity[] = []
        const layers = [...borehole.layers].sort((left, right) => left.sort_order - right.sort_order)
        for (const layer of layers) {
            const thickness = Math.max(layer.thickness, 0)
            if (thickness <= 0) {
                continue
            }

            const centerHeight = borehole.elevation - (layer.top_depth + thickness / 2) * BOREHOLE_VERTICAL_EXAGGERATION
            const layerColor = Color.fromCssColorString(layer.color || DEFAULT_BOREHOLE_LAYER_COLOR)
            const entity = entityManager.addCylinder({
                id: `borehole-layer-${borehole.id}-${layer.sort_order}`,
                name: `${borehole.name}-${layer.layer_name}`,
                position: { lon: borehole.longitude, lat: borehole.latitude, height: centerHeight },
                length: Math.max(thickness * BOREHOLE_VERTICAL_EXAGGERATION, BOREHOLE_MIN_VISUAL_LENGTH),
                topRadius: BOREHOLE_VISUAL_RADIUS,
                bottomRadius: BOREHOLE_VISUAL_RADIUS,
                color: layerColor.withAlpha(0.8),
                outlineColor: layerColor.withAlpha(0.95),
                tag: 'borehole-layer-model',
            })
            entity.properties = new PropertyBag({
                domainType: 'borehole-layer-model',
                targetId: borehole.id,
                layerName: layer.layer_name,
                tag: 'borehole-layer-model',
            })
            layerEntities.push(entity)
        }

        if (layerEntities.length > 0) {
            targetMap.set(borehole.id, layerEntities)
        }
    }
}

/** 添加边界面与边界线实体并写入目标映射。 */
export function addBoundaryEntities(
    entityManager: EntityManager,
    boundaries: BoundaryRegion[],
    targetMap: Map<string, Entity[]>,
): void {
    for (const boundary of boundaries) {
        const positions = degreesArrayToCartesianArray(
            boundary.coordinates.map((item) => ({ lon: item[0], lat: item[1], height: 0 })),
        )
        const color = pickBoundaryColor(boundary.type)
        const polygon = entityManager.addPolygon({
            id: `boundary-${boundary.id}`,
            name: boundary.name,
            positions,
            color: color.withAlpha(boundary.type === 'mine' ? 0.12 : 0.18),
            outlineColor: color.withAlpha(0.95),
            outlineWidth: boundary.type === 'mine' ? 2 : 1,
            tag: 'boundary',
        })
        const polyline = entityManager.addPolyline({
            id: `boundary-outline-${boundary.id}`,
            name: `${boundary.name}-outline`,
            positions,
            width: boundary.type === 'mine' ? 4 : 3,
            color: color.withAlpha(0.95),
            clampToGround: true,
            tag: 'boundary',
        })

        const boundaryProperties = new PropertyBag({
            domainType: 'boundary',
            targetId: boundary.id,
            boundaryType: boundary.type,
            tag: 'boundary',
        })
        polygon.properties = boundaryProperties
        polyline.properties = boundaryProperties

        targetMap.set(boundary.id, [polygon, polyline])
    }
}

/** 根据全部有效空间钻孔计算矩形范围。 */
export function buildBoreholeRectangle(boreholes: Borehole[]): Rectangle | null {
    const spatialBoreholes = boreholes.filter(hasSpatialPosition)
    if (spatialBoreholes.length === 0) {
        return null
    }

    const longitudes = spatialBoreholes.map((item) => item.longitude)
    const latitudes = spatialBoreholes.map((item) => item.latitude)
    return Rectangle.fromDegrees(
        Math.min(...longitudes) - 0.02,
        Math.min(...latitudes) - 0.02,
        Math.max(...longitudes) + 0.02,
        Math.max(...latitudes) + 0.02,
    )
}

/** 根据单个边界对象计算矩形范围。 */
export function buildBoundaryRectangle(boundary: BoundaryRegion): Rectangle {
    const longitudes = boundary.coordinates.map((item) => item[0])
    const latitudes = boundary.coordinates.map((item) => item[1])
    return Rectangle.fromDegrees(
        Math.min(...longitudes) - 0.01,
        Math.min(...latitudes) - 0.01,
        Math.max(...longitudes) + 0.01,
        Math.max(...latitudes) + 0.01,
    )
}

/** 根据专题图边界计算矩形范围。 */
export function buildRasterRectangle(raster: RasterLayer): Rectangle {
    return Rectangle.fromDegrees(raster.bounds.west, raster.bounds.south, raster.bounds.east, raster.bounds.north)
}
