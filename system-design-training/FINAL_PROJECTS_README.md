# 🏗️ FINAL PROJECTS — Industry-Level System Design
### Three Production-Grade Projects for Your Resume

---

## 📋 Overview

These three projects are designed to demonstrate your system design knowledge at an industry level. Each project covers a different domain and different architectural challenges.

**Projects:**
1. 🔗 **SnapLink** — Scalable URL Shortener with Analytics
2. 💬 **ChatWave** — Real-Time Chat & Notification System
3. 🛒 **MarketFlow** — High-Traffic E-Commerce Order Processing System

Complete all three. Add them to GitHub with proper READMEs. Reference them in interviews and job applications.

---

## 🏗️ PROJECT 1: SnapLink — Scalable URL Shortener

### Problem Statement

Build a URL shortening service (similar to bit.ly) that can:
- Shorten long URLs to compact codes
- Redirect users from short URL to original URL
- Track analytics (clicks, geography, devices)
- Support custom aliases
- Handle 10,000+ redirects per second at peak

### Features

- **Core:** Shorten URL, Redirect, Custom alias
- **Analytics:** Click tracking, geographic breakdown, device type, referrer
- **User accounts:** Personal dashboard with URL history
- **Link management:** Expiry dates, disable links, edit destination
- **API:** Public API with rate limiting

### Functional Requirements

- User provides a long URL, system returns a short URL (7 chars by default)
- Clicking a short URL redirects user to the original URL in < 50ms
- Users can register to manage their URLs
- Analytics data is available per link (total clicks, unique clicks, etc.)
- Links can have expiry dates after which they return 410 Gone
- Custom aliases (e.g., `/mycompany` instead of `/xK9pQm`)
- Rate limit: 10 URL creations/minute per unauthenticated user

### Non-Functional Requirements

- **Availability:** 99.9% uptime
- **Latency:** Redirect in < 50ms (P95)
- **Scale:** 1 billion stored URLs, 10,000 redirects/second at peak
- **Durability:** No URL data loss
- **Security:** No phishing/malicious URL hosting

### Suggested Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend API | Django REST Framework |
| Database (primary) | PostgreSQL |
| Cache | Redis |
| URL code generation | Base62 encoding + auto-increment ID |
| Analytics queue | Celery + Redis |
| Analytics storage | ClickHouse or PostgreSQL (time-series partitioned) |
| CDN/Redirect edge | Cloudflare Workers (optional, for < 5ms redirect) |
| Deployment | Docker + Nginx + Gunicorn |

### System Design Requirements

Your implementation/design must include:
1. Database schema design
2. URL shortening algorithm
3. Redis caching strategy for redirects
4. Analytics pipeline (how clicks are tracked without slowing redirects)
5. Rate limiting implementation
6. API authentication (JWT)
7. Architecture diagram
8. Deployment configuration

---

## 🏗️ PROJECT 2: ChatWave — Real-Time Chat & Notification System

### Problem Statement

Build a real-time messaging platform (similar to Slack/WhatsApp) that supports:
- Direct messages between users
- Group channels (up to 1,000 members)
- Real-time message delivery via WebSockets
- Message history and search
- Online presence indicators
- Push notifications for offline users
- File/image sharing

### Features

- **Messaging:** DM and group channels, message threads
- **Real-time:** WebSocket connections for instant delivery
- **Presence:** Online/offline/away status, "typing..." indicators
- **Notifications:** In-app and push notifications (FCM integration)
- **Search:** Full-text search across messages
- **Media:** Image uploads with thumbnail generation
- **Reactions:** Emoji reactions on messages

### Functional Requirements

- Users connect via WebSocket on login
- Messages are delivered in real-time to all connected members of a channel
- Users who are offline receive messages when they reconnect
- Message history is paginated (newest first, load older on scroll)
- Online status is visible to contacts
- Push notifications sent to offline users via FCM
- Images are uploaded, stored, and thumbnails generated asynchronously

### Non-Functional Requirements

- **Latency:** Message delivery < 100ms for online users
- **Scale:** 100,000 concurrent WebSocket connections
- **Storage:** Retain 1 year of message history
- **Availability:** 99.95% uptime
- **Media:** Image uploads up to 25MB

### Suggested Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend API | Django Channels (WebSocket) + DRF |
| Message Broker | Redis (Pub/Sub for WebSocket broadcasting) |
| Database | PostgreSQL (messages, users, channels) |
| Search | Elasticsearch (full-text message search) |
| File Storage | AWS S3 + CloudFront CDN |
| Thumbnail Generation | Celery + Pillow |
| Push Notifications | Firebase Cloud Messaging (FCM) |
| Presence | Redis (user online status) |
| Deployment | Docker + Nginx + Daphne (ASGI server) |

### System Design Requirements

Your design must address:
1. WebSocket connection management at scale
2. Message fanout strategy for group channels
3. Offline message delivery mechanism
4. Presence system design
5. Media upload and processing pipeline
6. Message search architecture
7. Database schema for messages (considering performance at scale)
8. How the system handles sudden WebSocket disconnections

---

## 🏗️ PROJECT 3: MarketFlow — High-Traffic E-Commerce Order Processing

### Problem Statement

Build the order processing backend for a high-traffic e-commerce platform (similar to Daraz/Shopify) that handles:
- Product catalog with inventory management
- Shopping cart (persistent across devices)
- Flash sale support (1000x normal traffic spikes)
- Order placement with payment processing
- Order lifecycle management (placed → confirmed → shipped → delivered)
- Seller dashboard and buyer order history

### Features

- **Catalog:** Product listing, search, filtering, categories
- **Inventory:** Real-time stock tracking, reservation system for carts
- **Cart:** Persistent, synced across devices, expires after 7 days
- **Orders:** Place order, payment, confirmation, status tracking
- **Flash Sales:** Limited stock, timer-based activation, fair queuing
- **Notifications:** Order status updates via email + SMS
- **Admin/Seller:** Inventory management, order management dashboard

### Functional Requirements

- Users can browse products and add to cart
- Cart is saved even when user logs out (synced by user_id)
- Stock is soft-reserved for 15 minutes when in cart
- Order placement: atomically deduct inventory + create order + trigger payment
- If payment fails, inventory reservation is released
- Order has states: pending → paid → processing → shipped → delivered → (returned)
- Flash sale: Product goes from ₹999 to ₹99 for 1 hour, 100 units only
- All order state changes trigger async notifications

### Non-Functional Requirements

- **Scale:** 100,000 orders/day normal; 10x (1M orders/day) during flash sales
- **Consistency:** Inventory must be accurate (no overselling)
- **Latency:** Product page load < 200ms; order placement < 500ms
- **Availability:** 99.99% for checkout (high business impact)

### Suggested Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend API | Django REST Framework |
| Database | PostgreSQL (orders, inventory, users) |
| Cache | Redis (cart, sessions, flash sale counters) |
| Search | Elasticsearch (product search) |
| Queue | Celery + Redis (email, SMS, analytics) |
| Payment | Stripe/Bkash API integration mock |
| File Storage | AWS S3 (product images) |
| Deployment | Docker Compose (dev), Kubernetes (prod design) |

### System Design Requirements

1. Inventory management without overselling (atomic operations)
2. Cart design with Redis (data structure choice and why)
3. Flash sale implementation (preventing race conditions)
4. Order placement as a database transaction
5. Saga pattern for order → payment → inventory flow
6. Background job design for notifications
7. How to scale to 10x traffic during flash sales
8. Database sharding strategy for orders at scale

---

## 📐 Architecture Diagrams

### Project 1: SnapLink Architecture

```
                        ┌─────────────────────────────────────────────┐
                        │                  SnapLink                    │
                        └─────────────────────────────────────────────┘

[Browser/App]                                              [Analytics Dashboard]
     │                                                           │
     │ HTTPS                                                     │
     ▼                                                           │
[Nginx Load Balancer]                                           │
  ├── /api/* ──────────→ [Django API Servers (x3)]              │
  └── /{code} ─────────→ [Redirect Service]                     │
                               │                                │
                        [Redis Cache]                           │
                        (short_code → long_url)                 │
                               │ cache miss                     │
                               ▼                                │
                        [PostgreSQL Primary]                    │
                               │                                │
                        [PostgreSQL Replica]                    │
                               │ on redirect                    │
                        [Celery Worker] ────────────────────────┘
                        (async analytics)
                               │
                        [Analytics DB]
                        (ClickHouse/PostgreSQL)
```

### Project 2: ChatWave Architecture

```
[Mobile/Web Client]
     │ WebSocket + HTTPS
     ▼
[Nginx (Reverse Proxy)]
  ├── /api/* ──→ [Django REST API (Gunicorn)]
  └── /ws/*  ──→ [Django Channels (Daphne ASGI)] ←→ [Redis Pub/Sub]
                         │                                │
                  [PostgreSQL DB]               [WebSocket Server 2]
                  (messages, users)             [WebSocket Server 3]
                         │
                  [Celery Workers]
                  ├── [FCM Notifications]
                  ├── [Email]
                  └── [Thumbnail Gen] ──→ [S3 Storage]
                                              │
                                         [CloudFront CDN]
```

### Project 3: MarketFlow Architecture

```
[Client Browser/App]
     │
     ▼
[Nginx Load Balancer]
     │
     ├──→ [Django API Servers]
     │         │              │
     │    [PostgreSQL]   [Redis]
     │    (orders, inv)  (cart, sessions, flash sale)
     │         │
     │    [Elasticsearch]
     │    (product search)
     │
     └──→ [Celery Workers]
               ├── Queue: critical  → Payment callbacks, Order updates
               ├── Queue: email     → Order confirmations
               ├── Queue: sms       → Status notifications
               └── Queue: analytics → Event tracking

[Admin Dashboard] ──→ [Django Admin / Separate Admin API]
```

---

## 🚀 Setup Instructions (for all projects)

### Prerequisites

```bash
# Required
Python 3.11+
Docker + Docker Compose
PostgreSQL 15+
Redis 7+
Node.js 20+ (for any frontend)
```

### Local Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/project-name
cd project-name

# 2. Create environment file
cp .env.example .env
# Edit .env with your local values

# 3. Start with Docker Compose
docker-compose up -d

# 4. Run migrations
docker-compose exec api python manage.py migrate

# 5. Create superuser
docker-compose exec api python manage.py createsuperuser

# 6. Load sample data (if available)
docker-compose exec api python manage.py loaddata fixtures/sample_data.json

# 7. Access the app
# API: http://localhost:8000/api/
# Admin: http://localhost:8000/admin/
# API Docs: http://localhost:8000/api/docs/
```

### Environment Variables (.env)

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@db:5432/dbname

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# AWS S3 (Project 2 & 3)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_STORAGE_BUCKET_NAME=your-bucket
AWS_S3_REGION_NAME=ap-southeast-1

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=your-app-password

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=15
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
```

---

## 📁 Folder Structure

```
project-name/
├── docker-compose.yml
├── docker-compose.prod.yml
├── Dockerfile
├── .env.example
├── README.md
│
├── backend/                    # Django project
│   ├── manage.py
│   ├── requirements.txt
│   ├── requirements.dev.txt
│   │
│   ├── config/                 # Django settings
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   ├── celery.py
│   │   └── wsgi.py
│   │
│   ├── apps/
│   │   ├── users/              # Authentication, profiles
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   └── tests/
│   │   │
│   │   ├── core/               # Project-specific main app
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── tasks.py        # Celery tasks
│   │   │   ├── services.py     # Business logic layer
│   │   │   ├── urls.py
│   │   │   └── tests/
│   │   │
│   │   └── analytics/          # Analytics app (Project 1)
│   │       ├── models.py
│   │       ├── tasks.py
│   │       └── views.py
│   │
│   └── shared/                 # Shared utilities
│       ├── cache.py            # Redis helpers
│       ├── pagination.py
│       ├── permissions.py
│       └── exceptions.py
│
├── nginx/
│   ├── nginx.conf
│   └── conf.d/
│       └── default.conf
│
├── scripts/
│   ├── start.sh
│   └── celery_start.sh
│
└── docs/
    ├── api.md                  # API documentation
    ├── architecture.md         # Architecture decisions
    └── deployment.md           # Deployment guide
```

---

## 🌐 API Design Summary

### Project 1: SnapLink API

```
POST   /api/v1/auth/register        Register user
POST   /api/v1/auth/login           Get JWT tokens
POST   /api/v1/auth/refresh         Refresh access token

POST   /api/v1/urls/                Shorten a URL
GET    /api/v1/urls/                List user's URLs
GET    /api/v1/urls/{id}/           Get URL details
PATCH  /api/v1/urls/{id}/           Update URL (alias, expiry)
DELETE /api/v1/urls/{id}/           Delete URL
GET    /api/v1/urls/{id}/analytics/ Get click analytics

GET    /{short_code}                Redirect (not under /api/)
```

### Project 2: ChatWave API

```
POST   /api/v1/auth/register
POST   /api/v1/auth/login

GET    /api/v1/channels/            List user's channels
POST   /api/v1/channels/            Create channel
GET    /api/v1/channels/{id}/messages/  Get message history
POST   /api/v1/channels/{id}/messages/  Send message (REST fallback)

GET    /api/v1/users/search/        Search users

WebSocket: ws://.../ws/chat/{channel_id}/
  Client → Server: {"type": "message", "content": "Hello!"}
  Client → Server: {"type": "typing"}
  Server → Client: {"type": "message", "sender": {...}, "content": "...", "timestamp": "..."}
  Server → Client: {"type": "presence", "user_id": 123, "status": "online"}
```

### Project 3: MarketFlow API

```
GET    /api/v1/products/            List products (filter, search, paginate)
GET    /api/v1/products/{id}/       Product detail

GET    /api/v1/cart/                Get current cart
POST   /api/v1/cart/items/          Add item to cart
PATCH  /api/v1/cart/items/{id}/     Update quantity
DELETE /api/v1/cart/items/{id}/     Remove item

POST   /api/v1/orders/              Place order
GET    /api/v1/orders/              Order history
GET    /api/v1/orders/{id}/         Order detail
POST   /api/v1/orders/{id}/cancel/  Cancel order

POST   /api/v1/payments/{order_id}/ Process payment
```

---

## 🚢 Deployment Steps

### Local (Docker Compose)

```bash
docker-compose up --build
```

### Production (Simplified)

```bash
# 1. Build and push Docker image
docker build -t your-registry/app:v1.0.0 .
docker push your-registry/app:v1.0.0

# 2. Deploy to server
docker-compose -f docker-compose.prod.yml up -d

# 3. Run migrations
docker-compose exec api python manage.py migrate

# 4. Collect static files
docker-compose exec api python manage.py collectstatic --no-input
```

### Sample docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru

  api:
    build: .
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - static_files:/app/staticfiles

  worker:
    build: .
    command: celery -A config worker -l info -Q default,email,critical
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - api
      - redis

  beat:
    build: .
    command: celery -A config beat -l info
    depends_on:
      - worker

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - static_files:/var/www/static
      - ./nginx/certs:/etc/nginx/certs
    depends_on:
      - api

volumes:
  postgres_data:
  static_files:
```

---

## 📄 Resume Descriptions

Use these descriptions when adding projects to your CV/LinkedIn:

### Project 1: SnapLink

> **SnapLink — Scalable URL Shortener** | Django, Redis, PostgreSQL, Celery, Docker
>
> Designed and built a high-throughput URL shortening service handling 10,000 redirects/second. Implemented Redis-based caching layer achieving < 5ms redirect latency for cached URLs (95% cache hit rate). Built async analytics pipeline using Celery to track click metrics without impacting redirect performance. Designed rate limiting using Redis sliding window algorithm. Containerized with Docker, deployed behind Nginx with connection pooling.

### Project 2: ChatWave

> **ChatWave — Real-Time Messaging System** | Django Channels, WebSocket, Redis, PostgreSQL, Elasticsearch
>
> Built a real-time chat platform supporting 100,000 concurrent WebSocket connections using Django Channels and Redis Pub/Sub for message fanout. Implemented online presence system using Redis with TTL-based expiry. Designed asynchronous push notification pipeline (FCM) with Celery for offline users. Added full-text message search using Elasticsearch. Built media processing pipeline for image uploads with async thumbnail generation and S3 storage.

### Project 3: MarketFlow

> **MarketFlow — E-Commerce Order Processing** | Django, PostgreSQL, Redis, Celery, Elasticsearch, Docker
>
> Architected high-traffic e-commerce backend supporting 1M orders/day during flash sales. Designed inventory reservation system using Redis atomic operations to prevent overselling during concurrent requests. Implemented Saga pattern for distributed order-payment-inventory consistency. Built flash sale system using Redis counters with Lua scripts for atomic stock management. Designed horizontally scalable stateless API with Redis session management, enabling zero-downtime deployments.

---

**➡️ Next: PROJECT_1_SOLUTION.md, PROJECT_2_SOLUTION.md, PROJECT_3_SOLUTION.md**
