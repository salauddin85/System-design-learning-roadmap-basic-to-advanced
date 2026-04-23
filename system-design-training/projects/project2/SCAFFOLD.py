# ChatWave — Project 2 Starter Scaffold
# Use this alongside PROJECT_2_SOLUTION.md to build the full system.

# ─────────────────────────────────────────────
# FOLDER STRUCTURE
# ─────────────────────────────────────────────
#
# chatwave/
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
# │   ├── asgi.py          ← Important! ASGI for WebSockets
# │   └── celery.py
# │
# ├── apps/
# │   ├── users/           (auth, profile, FCM token)
# │   ├── chat/            (channels, messages, consumer)
# │   ├── presence/        (online/offline/typing)
# │   ├── notifications/   (FCM push, email)
# │   └── media/           (S3 upload, thumbnails)
# │
# └── nginx/
#     └── conf.d/
#         └── default.conf  ← Must handle WebSocket upgrade!

# ─────────────────────────────────────────────
# requirements.txt
# ─────────────────────────────────────────────
REQUIREMENTS = """
Django==4.2.13
channels==4.0.0
channels-redis==4.2.0
daphne==4.1.0
djangorestframework==3.15.1
djangorestframework-simplejwt==5.3.1
django-cors-headers==4.3.1
django-environ==0.11.2
celery==5.3.6
redis==5.0.4
django-redis==5.4.0
psycopg2-binary==2.9.9
elasticsearch-dsl==8.13.0
firebase-admin==6.5.0
boto3==1.34.0
Pillow==10.3.0
python-json-logger==2.0.7
drf-spectacular==0.27.2
"""

# ─────────────────────────────────────────────
# config/asgi.py  — CRITICAL for WebSocket support
# ─────────────────────────────────────────────
ASGI_CONFIG = """
import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.chat.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
"""

# ─────────────────────────────────────────────
# apps/chat/models.py
# ─────────────────────────────────────────────
CHAT_MODELS = """
from django.db import models
from django.conf import settings


class Channel(models.Model):
    TYPE_DIRECT = 'direct'
    TYPE_GROUP = 'group'
    TYPE_CHOICES = [(TYPE_DIRECT, 'Direct'), (TYPE_GROUP, 'Group')]

    name        = models.CharField(max_length=100, blank=True)
    type        = models.CharField(max_length=10, choices=TYPE_CHOICES)
    created_by  = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                    on_delete=models.SET_NULL, related_name='created_channels')
    avatar_url  = models.TextField(blank=True)
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'channels'


class ChannelMember(models.Model):
    ROLE_ADMIN = 'admin'
    ROLE_MEMBER = 'member'
    ROLE_CHOICES = [(ROLE_ADMIN, 'Admin'), (ROLE_MEMBER, 'Member')]

    channel      = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='members')
    user         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                     related_name='channel_memberships')
    role         = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    joined_at    = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'channel_members'
        unique_together = [('channel', 'user')]
        indexes = [models.Index(fields=['user'])]


class Message(models.Model):
    TYPE_TEXT   = 'text'
    TYPE_IMAGE  = 'image'
    TYPE_FILE   = 'file'
    TYPE_SYSTEM = 'system'
    TYPE_CHOICES = [(TYPE_TEXT, 'Text'), (TYPE_IMAGE, 'Image'),
                    (TYPE_FILE, 'File'), (TYPE_SYSTEM, 'System')]

    channel      = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='messages')
    sender       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                     related_name='sent_messages')
    content      = models.TextField(blank=True)
    message_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_TEXT)
    media_url    = models.TextField(blank=True)
    reply_to     = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    is_edited    = models.BooleanField(default=False)
    is_deleted   = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'messages'
        indexes = [
            models.Index(fields=['channel', '-created_at']),
        ]
        ordering = ['created_at']
"""

# ─────────────────────────────────────────────
# apps/chat/routing.py
# ─────────────────────────────────────────────
ROUTING = """
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<channel_id>\\d+)/$', consumers.ChatConsumer.as_asgi()),
]
"""

# ─────────────────────────────────────────────
# nginx/conf.d/default.conf — WebSocket support
# ─────────────────────────────────────────────
NGINX_CONFIG = """
upstream django_api {
    server api:8000;
}

map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

server {
    listen 80;
    server_name localhost;

    location /api/ {
        proxy_pass http://django_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket support — critical!
    location /ws/ {
        proxy_pass http://django_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_read_timeout 86400;  # Keep WebSocket alive for 24h
    }

    location /static/ {
        alias /var/www/static/;
    }
}
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
      POSTGRES_DB: chatwave
      POSTGRES_USER: chatwave
      POSTGRES_PASSWORD: chatwave_pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru

  api:
    build: .
    command: daphne -b 0.0.0.0 -p 8000 config.asgi:application
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://chatwave:chatwave_pass@db:5432/chatwave
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - DEBUG=True
    depends_on:
      - db
      - redis

  worker:
    build: .
    command: celery -A config worker -l info -Q default,notifications,media
    volumes:
      - .:/app
    environment:
      - DATABASE_URL=postgresql://chatwave:chatwave_pass@db:5432/chatwave
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis

  elasticsearch:
    image: elasticsearch:8.13.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
    depends_on:
      - api

volumes:
  postgres_data:
"""

print("ChatWave Scaffold ready.")
print("Key difference from Project 1: Uses Daphne (ASGI) instead of Gunicorn (WSGI)")
print("WebSocket consumer lives in apps/chat/consumers.py")
print("Refer to PROJECT_2_SOLUTION.md for the full consumer implementation.")
