# MineScope3D

MineScope3D 是一个基于 Vue 3 + Cesium + ECharts 的矿区三维可视化单页系统，后端使用 Flask 提供本地文件驱动的空间数据服务。

当前版本后端不依赖数据库，直接读取 `backend/data` 与 `backend/static` 中的数据文件，支持钻孔、边界、栅格和 3D Tiles 四类能力。

## 技术栈

- 前端: Vue 3, TypeScript, Vite, Element Plus, Cesium, ECharts, Pinia
- 后端: Flask, Flask-Cors
- 数据处理: openpyxl, pyproj, pyshp, Pillow

## 目录结构

```text
MineScope3D/
├─ src/                        # 前端源码
├─ backend/
│  ├─ routes/                  # API 路由层
│  ├─ services/                # 业务与数据解析层
│  ├─ app.py                   # Flask 入口
│  ├─ config.py                # 配置与环境变量
│  ├─ data/                    # 本地导入数据目录
│  └─ static/                  # 栅格预览与 3DTiles 资源
└─ public/
```

## 环境要求

- Node.js >= 18
- Python >= 3.10

## 环境变量

1. 复制 `.env.example` 为 `.env`
2. 按本机运行参数修改配置

主要变量说明:

- `BACKEND_HOST`: Flask 监听地址，默认 `0.0.0.0`
- `BACKEND_PORT`: Flask 监听端口，默认 `8000`
- `BACKEND_DEBUG`: Flask 调试开关，默认 `true`
- `CORS_ALLOWED_ORIGINS`: 前端允许来源
- `VITE_CESIUM_TERRAIN_URL`: 前端地形服务 URL（可选，配置后优先使用）
- `VITE_CESIUM_ION_ACCESS_TOKEN`: Cesium ion 访问令牌（可选，未配置 `VITE_CESIUM_TERRAIN_URL` 时用于 World Terrain）

## 安装依赖

前端依赖:

```bash
npm install
```

后端依赖:

```bash
cd backend
pip install -r requirements.txt
```

## 数据导入

将源数据放入以下目录即可，后端接口会在请求时自动扫描并解析:

- 钻孔/分层 Excel: `backend/data/boreholes` 与 `backend/data/location`
- 边界 SHP: `backend/data/shp`
- 栅格 TIFF/TFW: `backend/data/tif`

## 启动项目

启动后端:

```bash
cd backend
python app.py
```

启动前端:

```bash
npm run dev
```

默认访问:

- 前端: `http://127.0.0.1:5173`
- 后端: `http://127.0.0.1:8000`

## 后端 API

基础前缀: `/api`

钻孔:

- `GET /api/boreholes/`
- `GET /api/boreholes/geojson/`
- `GET /api/boreholes/{borehole_id}/`
- `GET /api/boreholes/{borehole_id}/layers/`

边界:

- `GET /api/boundaries/`
- `GET /api/boundaries/geojson/`
- `GET /api/boundaries/{boundary_id}/`

栅格:

- `GET /api/rasters/`
- `GET /api/rasters/files/{raster_id}/`
- `GET /api/rasters/{raster_id}/`

统计:

- `GET /api/dashboard/overview/`
- `GET /api/dashboard/layer-distribution/`
- `GET /api/dashboard/workface-boreholes/`
- `GET /api/dashboard/borehole-depth-distribution/`
- `GET /api/dashboard/tilesets/`
- `GET /api/dashboard/tilesets/current/`
- `GET /api/dashboard/tilesets/{tileset_id}/`
- `GET /api/dashboard/tilesets/{tileset_id}/{resource_path}`

## 常见问题

1. 前端出现接口失败
	- 前端内置了 mock fallback，后端不可用时会降级到演示数据
	- 请确认 Flask 后端已在 `8000` 端口启动

## 开发建议

- 新增接口建议遵循“services 解析逻辑 -> routes 暴露 API”的固定流程
- 避免在路由层写重业务逻辑，保持目录职责清晰
