from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
STATIC_DIR = BASE_DIR / 'static'


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding='utf-8', errors='ignore').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def parse_csv_env(env_key: str, default: str) -> list[str]:
    value = os.getenv(env_key, default)
    return [item.strip() for item in value.split(',') if item.strip()]


for env_path in (BASE_DIR / '.env', BASE_DIR.parent / '.env'):
    load_env_file(env_path)

HOST = os.getenv('BACKEND_HOST', '0.0.0.0')
PORT = int(os.getenv('BACKEND_PORT', '8000'))
DEBUG = os.getenv('BACKEND_DEBUG', 'true').lower() == 'true'
CORS_ALLOWED_ORIGINS = parse_csv_env(
    'CORS_ALLOWED_ORIGINS',
    'http://127.0.0.1:5174,http://127.0.0.1:5173',
)
