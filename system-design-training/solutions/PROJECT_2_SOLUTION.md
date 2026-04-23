# 💬 PROJECT 2 SOLUTION: ChatWave — Real-Time Chat System

---

## 📐 System Design Explanation

### Core Requirements Analysis

**Key challenges:**
1. Real-time delivery of messages (WebSocket)
2. 100,000 concurrent WebSocket connections (horizontal scaling)
3. Message delivery to offline users
4. Presence (online/offline/typing)
5. Message history at scale

**Two critical paths:**
- **Online path:** Message → WebSocket → instant delivery (< 100ms)
- **Offline path:** Message → store → push notification → deliver on reconnect

---

## 🏗️ Architecture

```
                ┌───────────────────────────────────────────┐
                │                 ChatWave                   │
                └───────────────────────────────────────────┘

[Mobile/Web Client]
       │
       │ WSS (WebSocket) / HTTPS
       ▼
[Nginx] ──────── /api/* ──────────→ [Django REST API]
    │                                      │
    └───── /ws/* ──────────────────→ [Django Channels]   ←──→ [Redis Pub/Sub]
                                           │                      │
                                           │            [Channels Server 2]
                                           │            [Channels Server 3]
                                           │
                                    [PostgreSQL]
                                    (messages, channels, users)
                                           │
                                    [Elasticsearch]
                                    (message full-text search)

[Celery Workers]
    ├── FCM Push Notifications (offline users)
    ├── Email Notifications
    └── Image/File Processing → [S3] → [CloudFront CDN]

[Redis]
    ├── Channel Layer (Django Channels message routing)
    ├── Presence store (online/offline/typing)
    └── Cache (user data, channel membership)
```

---

## 🗄️ Database Design

```sql
-- Users
CREATE TABLE users (
    id           BIGSERIAL PRIMARY KEY,
    username     VARCHAR(50) UNIQUE NOT NULL,
    email        VARCHAR(255) UNIQUE NOT NULL,
    password     VARCHAR(255) NOT NULL,
    avatar_url   TEXT,
    fcm_token    TEXT,                    -- Firebase push notification token
    last_seen    TIMESTAMPTZ,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Channels (both DMs and group channels)
CREATE TABLE channels (
    id           BIGSERIAL PRIMARY KEY,
    name         VARCHAR(100),            -- NULL for DMs
    type         VARCHAR(10) NOT NULL,    -- 'direct' or 'group'
    created_by   BIGINT REFERENCES users(id),
    avatar_url   TEXT,
    description  TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Channel Members
CREATE TABLE channel_members (
    channel_id   BIGINT REFERENCES channels(id) ON DELETE CASCADE,
    user_id      BIGINT REFERENCES users(id) ON DELETE CASCADE,
    role         VARCHAR(20) DEFAULT 'member',  -- admin, member
    joined_at    TIMESTAMPTZ DEFAULT NOW(),
    last_read_at TIMESTAMPTZ DEFAULT NOW(),      -- for unread count
    PRIMARY KEY (channel_id, user_id)
);

CREATE INDEX idx_channel_members_user ON channel_members(user_id);

-- Messages
CREATE TABLE messages (
    id           BIGSERIAL PRIMARY KEY,
    channel_id   BIGINT NOT NULL REFERENCES channels(id),
    sender_id    BIGINT NOT NULL REFERENCES users(id),
    content      TEXT,
    message_type VARCHAR(20) DEFAULT 'text',   -- text, image, file, system
    media_url    TEXT,                          -- S3 URL if image/file
    reply_to_id  BIGINT REFERENCES messages(id),
    is_edited    BOOLEAN DEFAULT FALSE,
    is_deleted   BOOLEAN DEFAULT FALSE,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    edited_at    TIMESTAMPTZ
) PARTITION BY RANGE (created_at);

-- Index for message history queries (most common: get recent messages in channel)
CREATE INDEX idx_messages_channel_created
    ON messages(channel_id, created_at DESC);

-- Reactions
CREATE TABLE message_reactions (
    message_id   BIGINT REFERENCES messages(id) ON DELETE CASCADE,
    user_id      BIGINT REFERENCES users(id) ON DELETE CASCADE,
    emoji        VARCHAR(10) NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (message_id, user_id, emoji)
);
```

### Why Partition Messages?

With 100B messages/day even at 1M users, the messages table grows extremely fast.
- Partition by month: each partition is manageable
- Queries typically filter by channel_id + recent date → scan is minimal
- Old data can be archived to cold storage

---

## 🔌 WebSocket Implementation

### Django Channels Setup

```python
# config/asgi.py
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.chat.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})

# apps/chat/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/chat/<int:channel_id>/', consumers.ChatConsumer.as_asgi()),
]
```

### Chat Consumer

```python
# apps/chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import redis.asyncio as aioredis

class ChatConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.channel_id = self.scope['url_route']['kwargs']['channel_id']
        self.user = self.scope['user']
        self.room_group_name = f'chat_{self.channel_id}'
        
        # Verify user has access to this channel
        if not await self.user_in_channel():
            await self.close(code=4003)  # Forbidden
            return
        
        # Join room group (Django Channels / Redis Pub/Sub)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Mark user as online in this channel
        await self.set_presence('online')
        
        # Notify others in channel that user came online
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'presence_update',
                'user_id': self.user.id,
                'status': 'online'
            }
        )
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Update presence
        await self.set_presence('offline')
        
        # Notify others
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'presence_update',
                'user_id': self.user.id,
                'status': 'offline'
            }
        )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket client."""
        data = json.loads(text_data)
        event_type = data.get('type')
        
        if event_type == 'message':
            await self.handle_message(data)
        elif event_type == 'typing':
            await self.handle_typing(data)
        elif event_type == 'read':
            await self.handle_read_receipt(data)
    
    async def handle_message(self, data):
        content = data.get('content', '').strip()
        if not content and not data.get('media_url'):
            return
        
        # Save to database
        message = await self.save_message(content, data.get('media_url'))
        
        # Broadcast to all channel members (including sender)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'sender': {
                        'id': self.user.id,
                        'username': self.user.username,
                        'avatar_url': self.user.avatar_url
                    },
                    'created_at': message.created_at.isoformat(),
                    'channel_id': self.channel_id,
                }
            }
        )
        
        # Notify offline users (fire and forget)
        from apps.notifications.tasks import notify_offline_members
        notify_offline_members.delay(
            channel_id=self.channel_id,
            message_id=message.id,
            sender_name=self.user.username
        )
    
    async def handle_typing(self, data):
        """Broadcast typing indicator to channel (not saved to DB)."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'username': self.user.username,
                'is_typing': data.get('is_typing', True)
            }
        )
    
    # Handlers for messages sent to this consumer from channel layer
    
    async def chat_message(self, event):
        """Send message to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator (only to others, not to self)."""
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            }))
    
    async def presence_update(self, event):
        """Send presence update to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'presence',
            'user_id': event['user_id'],
            'status': event['status']
        }))
    
    @database_sync_to_async
    def save_message(self, content, media_url=None):
        return Message.objects.create(
            channel_id=self.channel_id,
            sender=self.user,
            content=content,
            media_url=media_url
        )
    
    @database_sync_to_async
    def user_in_channel(self):
        return ChannelMember.objects.filter(
            channel_id=self.channel_id,
            user=self.user
        ).exists()
    
    async def set_presence(self, status: str):
        """Update user presence in Redis."""
        r = aioredis.from_url(settings.REDIS_URL)
        key = f"presence:user:{self.user.id}"
        if status == 'online':
            await r.setex(key, 300, status)  # Expires in 5 min (refresh on heartbeat)
        else:
            await r.delete(key)
        await r.close()
```

---

## 📡 Presence System

### Design

```
Redis Keys:
  presence:user:{user_id} → "online" (TTL: 300 seconds)

When user connects:
  SET presence:user:123 "online" EX 300

Every 60 seconds (client heartbeat):
  SETEX presence:user:123 300 "online"  ← renew TTL

When user disconnects (or heartbeat stops):
  Key expires automatically after 300s → user is "offline"

Typing indicator (ephemeral, not persisted):
  SET typing:{channel_id}:{user_id} "1" EX 5
  (Expires in 5 seconds — if user keeps typing, client refreshes)

Check if user is online:
  EXISTS presence:user:123  → 1 (online) or 0 (offline)

Bulk presence check:
  MGET presence:user:1 presence:user:2 presence:user:3
```

```python
# apps/presence/service.py

async def get_channel_presence(channel_id: int) -> dict:
    """Get online status for all members of a channel."""
    member_ids = await get_channel_member_ids(channel_id)
    keys = [f"presence:user:{uid}" for uid in member_ids]
    
    r = aioredis.from_url(settings.REDIS_URL)
    values = await r.mget(*keys)
    await r.close()
    
    return {
        uid: (val is not None and val.decode() == 'online')
        for uid, val in zip(member_ids, values)
    }
```

---

## 📱 Offline Push Notifications

```python
# apps/notifications/tasks.py
from celery import shared_task
import firebase_admin
from firebase_admin import messaging

@shared_task(queue='notifications', max_retries=3)
def notify_offline_members(channel_id: int, message_id: int, sender_name: str):
    """Send push notifications to offline channel members."""
    from apps.chat.models import ChannelMember, Message
    import redis
    
    r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    message = Message.objects.select_related('sender').get(id=message_id)
    
    # Get all members of the channel
    members = ChannelMember.objects.filter(
        channel_id=channel_id
    ).exclude(
        user_id=message.sender_id  # Don't notify the sender
    ).select_related('user')
    
    fcm_tokens = []
    for member in members:
        # Check if user is online
        is_online = r.exists(f"presence:user:{member.user_id}")
        if not is_online and member.user.fcm_token:
            fcm_tokens.append(member.user.fcm_token)
    
    if not fcm_tokens:
        return
    
    # Send FCM multicast
    notification = messaging.MulticastMessage(
        tokens=fcm_tokens,
        notification=messaging.Notification(
            title=sender_name,
            body=message.content[:100] if message.content else "Sent a media"
        ),
        data={
            'channel_id': str(channel_id),
            'message_id': str(message_id),
            'type': 'new_message'
        },
        android=messaging.AndroidConfig(
            priority='high',
            notification=messaging.AndroidNotification(
                sound='default',
                click_action='OPEN_CHANNEL'
            )
        ),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(sound='default')
            )
        )
    )
    
    response = messaging.send_multicast(notification)
    # Handle failed tokens (remove from DB if permanently invalid)
    for idx, result in enumerate(response.responses):
        if not result.success:
            if 'registration-token-not-registered' in str(result.exception):
                User.objects.filter(fcm_token=fcm_tokens[idx]).update(fcm_token=None)
```

---

## 🔍 Message Search (Elasticsearch)

```python
# apps/search/documents.py
from elasticsearch_dsl import Document, Text, Keyword, Date, Integer

class MessageDocument(Document):
    content = Text(analyzer='english')
    channel_id = Keyword()
    sender_id = Integer()
    sender_username = Keyword()
    created_at = Date()
    
    class Index:
        name = 'messages'
        settings = {
            'number_of_shards': 3,
            'number_of_replicas': 1
        }

# Sync messages to Elasticsearch via Celery (after save)
@shared_task
def index_message(message_id: int):
    message = Message.objects.select_related('sender').get(id=message_id)
    doc = MessageDocument(
        meta={'id': message_id},
        content=message.content,
        channel_id=message.channel_id,
        sender_id=message.sender_id,
        sender_username=message.sender.username,
        created_at=message.created_at
    )
    doc.save()

# Search API
def search_messages(query: str, channel_id: int, page: int = 1) -> list:
    search = MessageDocument.search()
    search = search.filter('term', channel_id=channel_id)
    search = search.query('match', content={
        'query': query,
        'fuzziness': 'AUTO'
    })
    search = search.highlight('content', fragment_size=100)
    search = search[(page-1)*20: page*20]  # Pagination
    
    results = search.execute()
    return [
        {
            'id': hit.meta.id,
            'content': hit.meta.highlight.content[0] if hasattr(hit.meta, 'highlight') else hit.content,
            'sender': hit.sender_username,
            'created_at': hit.created_at
        }
        for hit in results
    ]
```

---

## 📁 Media Upload Pipeline

```python
# apps/media/views.py
class MediaUploadView(APIView):
    """
    Step 1: Client requests a presigned S3 URL
    Step 2: Client uploads directly to S3 (bypasses our server!)
    Step 3: Client sends message with S3 URL
    """
    
    def post(self, request):
        file_type = request.data.get('file_type')  # 'image/jpeg', 'image/png', etc.
        file_size = request.data.get('file_size')
        
        # Validate
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if file_type not in allowed_types:
            return Response({'error': 'File type not allowed'}, status=400)
        if file_size > 25 * 1024 * 1024:  # 25MB limit
            return Response({'error': 'File too large'}, status=400)
        
        # Generate unique S3 key
        file_key = f"uploads/{request.user.id}/{uuid.uuid4()}/{int(time.time())}"
        
        # Generate presigned upload URL (valid for 15 minutes)
        s3_client = boto3.client('s3')
        presigned_url = s3_client.generate_presigned_post(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=file_key,
            Fields={'Content-Type': file_type},
            Conditions=[
                {'Content-Type': file_type},
                ['content-length-range', 1, 25 * 1024 * 1024]
            ],
            ExpiresIn=900  # 15 minutes
        )
        
        # Schedule thumbnail generation (will run after upload)
        generate_thumbnail.apply_async(
            args=[file_key, request.user.id],
            countdown=30  # Give 30s for upload to complete
        )
        
        return Response({
            'upload_url': presigned_url['url'],
            'upload_fields': presigned_url['fields'],
            'file_url': f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{file_key}"
        })


@shared_task
def generate_thumbnail(file_key: str, user_id: int):
    """Download from S3, resize, upload thumbnail back to S3."""
    s3 = boto3.client('s3')
    
    # Download original
    obj = s3.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=file_key)
    image_data = obj['Body'].read()
    
    # Generate thumbnail (200x200)
    from PIL import Image
    from io import BytesIO
    
    img = Image.open(BytesIO(image_data))
    img.thumbnail((200, 200), Image.LANCZOS)
    
    thumb_buffer = BytesIO()
    img.save(thumb_buffer, format='JPEG', quality=85)
    thumb_buffer.seek(0)
    
    # Upload thumbnail
    thumb_key = file_key.replace('uploads/', 'thumbnails/')
    s3.put_object(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=thumb_key,
        Body=thumb_buffer,
        ContentType='image/jpeg'
    )
```

---

## 📈 Scaling Strategy

### WebSocket Scaling Challenge

```
Problem: User A is connected to Server 1, User B to Server 2.
A sends message. How does B receive it?

Solution: Redis Pub/Sub as channel layer

Server 1 receives message from A:
→ Publishes to Redis channel: "chat_123" 

Redis broadcasts to all subscribers:
→ Server 2 (subscribed to "chat_123") receives the message
→ Server 2 forwards to User B's WebSocket connection

This is exactly what Django Channels + Redis Channel Layer does!
```

### Settings

```python
# config/settings/base.py
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis-cluster", 6379)],
            "capacity": 1500,           # Max messages in flight per channel
            "expiry": 10,              # Messages expire if not consumed in 10s
        },
    },
}
```

### Connection Capacity Calculation

```
Target: 100,000 concurrent WebSocket connections
Per Daphne (ASGI) worker: ~5,000 connections (async, so many per worker)
Workers needed: 100,000 / 5,000 = 20 Daphne processes
Servers needed: 20 processes / 4 per server = 5 servers

Redis channel layer overhead: minimal (just pub/sub, not persistent)
PostgreSQL: Use read replicas for message history queries
```

---

## ❌ Failure Handling

| Failure | Impact | Response |
|---------|--------|---------|
| WebSocket server crashes | Connected users disconnected | Client auto-reconnects; Django Channels stateless |
| Redis goes down | Message routing between servers fails | Fall back to single-server mode; alert |
| PostgreSQL primary down | Cannot save messages | Replica promoted; messages queued in Redis temporarily |
| FCM service down | Push notifications fail | Celery retry with backoff; messages still delivered when user reconnects |
| S3 unavailable | Media uploads fail | Return error to user; REST API not affected |

---

## ⚖️ Trade-offs

| Decision | Trade-off |
|----------|----------|
| Store all messages in PostgreSQL | Simple but needs partitioning at scale (vs. Cassandra which scales better for append-only writes) |
| Django Channels + Redis | Easy to implement but less performant than Erlang/Elixir (WhatsApp's choice) |
| FCM for push notifications | Easy to integrate, but extra latency vs custom socket push |
| Elasticsearch for search | Strong search features but extra infrastructure to manage |
| Presigned S3 uploads | Offloads upload bandwidth from our servers; client-side upload slightly more complex |
