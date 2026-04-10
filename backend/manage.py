#!/usr/bin/env python
"""Django 命令入口。"""
import os
import sys


def main():
    """启动 Django 管理命令。"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'minescope3d.settings')
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
