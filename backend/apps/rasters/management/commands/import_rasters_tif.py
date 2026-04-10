from django.core.management.base import BaseCommand

from apps.rasters.services import import_rasters_from_tif


class Command(BaseCommand):
    help = '将本地 TIFF 栅格导入 PostGIS'

    def handle(self, *args, **options):
        """执行栅格数据导入。"""
        result = import_rasters_from_tif(remove_missing=True)
        self.stdout.write(self.style.SUCCESS(f'已导入 {result["rasters"]} 条专题图层'))
