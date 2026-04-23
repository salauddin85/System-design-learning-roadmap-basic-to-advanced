# SnapLink — Project 1 Starter Scaffold
# This file documents the project structure and key starter code.
# Build on top of this scaffold using the FINAL_PROJECTS_README and PROJECT_1_SOLUTION as your guide.

# ─────────────────────────────────────────────
# FOLDER STRUCTURE
# ─────────────────────────────────────────────
#
# snaplink/
# ├── docker-compose.yml
# ├── Dockerfile
# ├── .env.example
# ├── requirements.txt
# ├── manage.py
# │
# ├── config/
# │   ├── settings/
# │   │   ├── base.py
# │   │   ├── development.py
# │   │   └── production.py
# │   ├── urls.py
# │   └── celery.py
# │
# ├── apps/
# │   ├── users/           (auth, JWT login/register)
# │   ├── urls/            (URL creation, redirect, management)
# │   └── analytics/       (click tracking, stats)
# │
# ├── shared/
# │   ├── base62.py
# │   ├── rate_limit.py
# │   └── cache.py
# │
# └── nginx/
#     └── conf.d/
#         └── default.conf

# ─────────────────────────────────────────────
# requirements.txt
# ─────────────────────────────────────────────
REQUIREMENTS = """
Django==4.2.13
djangorestframework==3.15.1
djangorestframework-simplejwt==5.3.1
django-cors-headers==4.3.1
django-environ==0.11.2
django-filter==24.2
celery==5.3.6
redis==5.0.4
django-redis==5.4.0
psycopg2-binary==2.9.9
gunicorn==22.0.0
Pillow==10.3.0
user-agents==2.2.0
python-json-logger==2.0.7
flower==2.0.1
drf-spectacular==0.27.2
"""

# ─────────────────────────────────────────────
# config/settings/base.py
# ─────────────────────────────────────────────
BASE_SETTINGS = """
import environ
from pathlib import Path

env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent.parent

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    # Local
    'apps.users',
    'apps.urls',
    'apps.analytics',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

DATABASES = {
    'default': env.db('DATABASE_URL'),
    'replica': env.db('DATABASE_REPLICA_URL', default=env('DATABASE_URL')),
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env('REDIS_URL', default='redis://localhost:6379/0'),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/1')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/2')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

AUTH_USER_MODEL = 'users.User'

BASE_URL = env('BASE_URL', default='http://localhost:8000')
"""

# ─────────────────────────────────────────────
# apps/users/models.py
# ─────────────────────────────────────────────
USERS_MODELS = """
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
import uuid

class User(AbstractBaseUser, PermissionsMixin):
    PLAN_FREE = 'free'
    PLAN_PRO = 'pro'
    PLAN_ENTERPRISE = 'enterprise'
    PLAN_CHOICES = [(PLAN_FREE, 'Free'), (PLAN_PRO, 'Pro'), (PLAN_ENTERPRISE, 'Enterprise')]

    email      = models.EmailField(unique=True)
    username   = models.CharField(max_length=50, unique=True)
    api_key    = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    plan       = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_FREE)
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
"""

# ─────────────────────────────────────────────
# apps/urls/models.py
# ─────────────────────────────────────────────
URL_MODELS = """
from django.db import models
from django.conf import settings

class URL(models.Model):
    short_code    = models.CharField(max_length=12, unique=True, db_index=True)
    long_url      = models.TextField()
    user          = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                      on_delete=models.SET_NULL, related_name='urls')
    custom_alias  = models.CharField(max_length=50, unique=True, null=True, blank=True)
    title         = models.CharField(max_length=500, blank=True)
    is_active     = models.BooleanField(default=True)
    expires_at    = models.DateTimeField(null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'urls'
        indexes = [
            models.Index(fields=['short_code']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.short_code} → {self.long_url[:50]}"

    @property
    def short_url(self):
        from django.conf import settings
        return f"{settings.BASE_URL}/{self.short_code}"


class Click(models.Model):
    url          = models.ForeignKey(URL, on_delete=models.CASCADE, related_name='clicks')
    clicked_at   = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_hash      = models.CharField(max_length=64, blank=True)
    country      = models.CharField(max_length=2, blank=True)
    city         = models.CharField(max_length=100, blank=True)
    device_type  = models.CharField(max_length=20, blank=True)
    os           = models.CharField(max_length=50, blank=True)
    browser      = models.CharField(max_length=50, blank=True)
    referrer     = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = 'clicks'
        indexes = [
            models.Index(fields=['url', '-clicked_at']),
        ]
"""

# ─────────────────────────────────────────────
# shared/base62.py
# ─────────────────────────────────────────────
BASE62_CODE = """
import string

CHARS = string.digits + string.ascii_lowercase + string.ascii_uppercase

def encode(num: int) -> str:
    if num == 0:
        return CHARS[0]
    result = []
    while num:
        result.append(CHARS[num % 62])
        num //= 62
    return ''.join(reversed(result))

def decode(code: str) -> int:
    num = 0
    for char in code:
        num = num * 62 + CHARS.index(char)
    return num
"""

# ─────────────────────────────────────────────
# docker-compose.yml
# ─────────────────────────────────────────────
DOCKER_COMPOSE = """
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: snaplink
      POSTGRES_USER: snaplink
      POSTGRES_PASSWORD: snaplink_pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"

  api:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://snaplink:snaplink_pass@db:5432/snaplink
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - DEBUG=True
    depends_on:
      - db
      - redis

  worker:
    build: .
    command: celery -A config worker -l info -Q default,analytics
    volumes:
      - .:/app
    environment:
      - DATABASE_URL=postgresql://snaplink:snaplink_pass@db:5432/snaplink
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis

  flower:
    build: .
    command: celery -A config flower --port=5555
    ports:
      - "5555:5555"
    depends_on:
      - worker

volumes:
  postgres_data:
"""

print("SnapLink Scaffold — Read this file and implement each section.")
print("Refer to PROJECT_1_SOLUTION.md for full implementation details.")
