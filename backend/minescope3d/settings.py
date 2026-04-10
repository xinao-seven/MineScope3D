"""MineScope3D 后端基础配置。"""
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


def load_env_file(env_path: Path):
    """加载 .env 文件中的键值到进程环境变量。"""
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding='utf-8', errors='ignore').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


for env_path in (BASE_DIR / '.env', BASE_DIR.parent / '.env'):
    load_env_file(env_path)


def resolve_library_path(env_key: str, fallback_paths: list[str]) -> str:
    """优先读取环境变量，否则使用存在的本地动态库路径。"""
    env_value = os.getenv(env_key, '').strip()
    if env_value:
        return env_value
    for candidate in fallback_paths:
        if Path(candidate).exists():
            return candidate
    return ''


if os.name == 'nt':
    GDAL_LIBRARY_PATH = resolve_library_path(
        'GDAL_LIBRARY_PATH',
        [
            r'C:\Program Files\PostgreSQL\18\bin\libgdal-35.dll',
            r'C:\Program Files\PostgreSQL\17\bin\libgdal-35.dll',
            r'C:\Program Files\PostgreSQL\16\bin\libgdal-35.dll',
        ],
    )
    GEOS_LIBRARY_PATH = resolve_library_path(
        'GEOS_LIBRARY_PATH',
        [
            r'C:\Program Files\PostgreSQL\18\bin\libgeos_c.dll',
            r'C:\Program Files\PostgreSQL\17\bin\libgeos_c.dll',
            r'C:\Program Files\PostgreSQL\16\bin\libgeos_c.dll',
        ],
    )

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'minescope3d-dev-secret')
DEBUG = os.getenv('DJANGO_DEBUG', 'true').lower() == 'true'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.gis',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'apps.boreholes',
    'apps.boundaries',
    'apps.rasters',
    'apps.dashboard',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'minescope3d.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'minescope3d.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DJANGO_DB_ENGINE', 'django.contrib.gis.db.backends.postgis'),
        'NAME': os.getenv('POSTGRES_DB', os.getenv('PGDATABASE', 'minegis')),
        'USER': os.getenv('POSTGRES_USER', os.getenv('PGUSER', 'postgres')),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', os.getenv('PGPASSWORD', '')),
        'HOST': os.getenv('POSTGRES_HOST', os.getenv('PGHOST', '127.0.0.1')),
        'PORT': os.getenv('POSTGRES_PORT', os.getenv('PGPORT', '5432')),
        'CONN_MAX_AGE': int(os.getenv('POSTGRES_CONN_MAX_AGE', '60')),
    },
}

db_schema = os.getenv('POSTGRES_SCHEMA', os.getenv('PGSCHEMA', 'public')).strip()
if db_schema:
    DATABASES['default']['OPTIONS'] = {'options': f'-c search_path={db_schema}'}

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://127.0.0.1:5174,http://127.0.0.1:5173').split(',')

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser'],
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'UNAUTHENTICATED_USER': None,
}
