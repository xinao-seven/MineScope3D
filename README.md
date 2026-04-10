# MineScope3D

MineScope3D 是一个基于 Vue 3 + Cesium + ECharts 的矿区三维可视化单页系统，后端使用 Django + PostGIS 提供空间数据服务。

当前版本已经完成从“本地文件直读”到“PostGIS 入库 + API 查询”的改造，支持钻孔、边界、栅格三类数据的导入、存储与展示。

## 技术栈

- 前端: Vue 3, TypeScript, Vite, Element Plus, Cesium, ECharts, Pinia
- 后端: Django, Django REST Framework, PostGIS
- 数据处理: openpyxl, pyproj, pyshp, Pillow

## 目录结构

```text
MineScope3D/
├─ src/                        # 前端源码
├─ backend/
│  ├─ apps/
│  │  ├─ boreholes/            # 钻孔与分层
│  │  ├─ boundaries/           # 边界
│  │  ├─ rasters/              # 栅格专题图
│  │  └─ dashboard/            # 统计接口与同步命令
│  ├─ data/                    # 本地导入数据目录
│  └─ minescope3d/             # Django 配置与总路由
└─ public/
```

## 环境要求

- Node.js >= 18
- Python >= 3.10
- PostgreSQL + PostGIS
- Windows 下建议安装 PostgreSQL 并包含 PostGIS（当前配置可自动探测常见 GDAL/GEOS 路径）

## 环境变量

1. 复制 `.env.example` 为 `.env`
2. 按本机数据库信息修改连接参数

主要变量说明:

- `DJANGO_DB_ENGINE`: 默认 `django.contrib.gis.db.backends.postgis`
- `POSTGRES_HOST/PORT/USER/PASSWORD/DB/SCHEMA`: Django 连接 PostGIS
- `PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE/PGSCHEMA`: 兼容键名
- `CORS_ALLOWED_ORIGINS`: 前端允许来源

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

## 初始化数据库

在 `backend` 目录执行:

```bash
python manage.py migrate
```

## 数据导入

将源数据放入以下目录后执行导入命令:

- 钻孔/分层 Excel: `backend/data/boreholes` 与 `backend/data/location`
- 边界 SHP: `backend/data/shp`
- 栅格 TIFF/TFW: `backend/data/tif`

可选命令:

```bash
# 单独导入
python manage.py import_borehole_excel
python manage.py import_boundaries_shp
python manage.py import_rasters_tif

# 一键导入
python manage.py sync_local_data
```

## 启动项目

启动后端:

```bash
cd backend
python manage.py runserver 0.0.0.0:8000
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
- `GET /api/rasters/{raster_id}/`

统计:

- `GET /api/dashboard/overview/`
- `GET /api/dashboard/layer-distribution/`
- `GET /api/dashboard/workface-boreholes/`
- `GET /api/dashboard/borehole-depth-distribution/`

## 常见问题

1. `Could not find the GDAL library`
	- Windows 下可在 `.env` 中显式配置 `GDAL_LIBRARY_PATH` 和 `GEOS_LIBRARY_PATH`

2. `Error loading psycopg2 or psycopg module`
	- 重新安装驱动: `pip install "psycopg[binary]>=3.2"`

3. 前端出现接口失败
	- 前端内置了 mock fallback，后端不可用时会降级到演示数据

## 开发建议

- 新增数据类型时优先遵循“模型 -> 迁移 -> 导入服务 -> 序列化器 -> 视图/路由”的固定流程
- 避免提交真实数据库密码或生产环境地址
