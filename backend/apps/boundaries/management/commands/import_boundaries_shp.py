from django.core.management.base import BaseCommand

from apps.boundaries.services import import_boundaries_from_shp


class Command(BaseCommand):
    help = '将本地 SHP 边界导入 PostGIS'

    def handle(self, *args, **options):
        """执行边界数据导入。"""
        result = import_boundaries_from_shp(replace_existing=True)
        self.stdout.write(self.style.SUCCESS(f'已导入 {result["boundaries"]} 条边界数据'))
