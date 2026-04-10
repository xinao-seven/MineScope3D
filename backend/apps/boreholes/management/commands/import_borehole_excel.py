from django.core.management.base import BaseCommand
from apps.boreholes.services.excel_import_service import import_boreholes_from_excel


class Command(BaseCommand):
    help = '将本地钻孔 Excel 数据导入 PostGIS'

    def handle(self, *args, **options):
        """执行钻孔数据导入。"""
        result = import_boreholes_from_excel(remove_missing=True)
        self.stdout.write(self.style.SUCCESS(f'已导入 {result["boreholes"]} 个钻孔，{result["layers"]} 条分层'))
