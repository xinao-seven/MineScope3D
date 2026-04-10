from django.core.management.base import BaseCommand

from apps.boreholes.services.excel_import_service import (
    import_boreholes_from_excel,
    sync_borehole_workface_names,
)
from apps.boundaries.services import import_boundaries_from_shp
from apps.rasters.services import import_rasters_from_tif


class Command(BaseCommand):
    help = '一键同步本地 Excel/SHP/TIFF 数据到 PostGIS'

    def handle(self, *args, **options):
        """按依赖顺序执行导入任务。"""
        borehole_result = import_boreholes_from_excel(remove_missing=True)
        boundary_result = import_boundaries_from_shp(replace_existing=True)
        workface_sync_result = sync_borehole_workface_names()
        raster_result = import_rasters_from_tif(remove_missing=True)

        self.stdout.write(self.style.SUCCESS('本地数据同步完成'))
        self.stdout.write(f'- 钻孔: {borehole_result["boreholes"]} 条, 分层: {borehole_result["layers"]} 条')
        self.stdout.write(f'- 边界: {boundary_result["boundaries"]} 条')
        self.stdout.write(
            f'- 工作面匹配回填: 检查 {workface_sync_result["checked"]} 条, 更新 {workface_sync_result["updated"]} 条'
        )
        self.stdout.write(f'- 栅格: {raster_result["rasters"]} 条')
