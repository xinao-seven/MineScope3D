from django.core.management.base import BaseCommand
from apps.boreholes.services.excel_import_service import load_boreholes


class Command(BaseCommand):
    help = '检查本地钻孔 Excel 文件解析结果'

    def handle(self, *args, **options):
        """输出本地钻孔 Excel 解析数量。"""
        boreholes = load_boreholes()
        self.stdout.write(self.style.SUCCESS(f'已解析 {len(boreholes)} 个本地钻孔，不执行数据库入库'))
