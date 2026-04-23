# 📗 System Design Training — INTERMEDIATE LEVEL
### Building Scalable, Production-Ready Systems

---

## 🧭 Introduction

Welcome to the Intermediate level!

You now understand the fundamentals. Here, we go deeper — how systems actually scale, how databases handle millions of records, how to design APIs that professionals use, and how to protect your system.

By the end of this module, you will think like a backend engineer at a growing product company.

---

## ✅ Prerequisites

Before starting this level, ensure you've completed all BASIC assignments and can:
- Explain DNS, HTTP, APIs confidently
- Design a basic client-server system
- Understand the difference between SQL and NoSQL
- Know what a load balancer and cache do

---

## 🗺️ Learning Roadmap

---

## STEP 1: Scaling Concepts — Horizontal vs Vertical (Deep Dive)

### 📖 Concept Explanation

We introduced this in basics. Now let's understand the engineering implications.

**Vertical Scaling (Scale Up):**
Increasing resources on a single machine.

```
+-------------------+       +-------------------+
|  Server           |  →    |  Server           |
|  4 vCPU           |       |  64 vCPU          |
|  16 GB RAM        |       |  256 GB RAM       |
|  500 GB SSD       |       |  4 TB SSD         |
+-------------------+       +-------------------+
```

**Limitations of Vertical Scaling:**
- Physical hardware limits (you can't add infinite RAM)
- Requires downtime during upgrade
- Very expensive at higher tiers
- Single point of failure remains

**Horizontal Scaling (Scale Out):**
Adding more machines (instances) to distribute the load.

```
                  [Load Balancer]
                 /       |       \
          [App-1]    [App-2]    [App-3]
            |           |          |
        [Shared Database or Each with own DB shard]
```

**Challenges with horizontal scaling:**
- Sessions must be externalized (use Redis, not in-memory)
- Shared state must be in a central store
- More complexity in deployment and coordination

### 🌍 Real-World Example: Django App Scaling

```python
# ❌ Bad for horizontal scaling: Storing session in memory
request.session['cart'] = cart_data  # Each server has different memory!

# ✅ Good for horizontal scaling: Session in Redis (shared)
# settings.py
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
    }
}
```

**Auto Scaling in AWS:**
AWS Auto Scaling Groups monitor CPU/memory and automatically add or remove servers.
```
CPU > 80% for 5 minutes → Add 2 more servers (scale out)
CPU < 20% for 10 minutes → Remove 2 servers (scale in, save money)
```

### ✅ Best Practices

- Design services to be stateless (any server can handle any request)
- Use cloud auto-scaling groups for elastic traffic
- Use a CDN to reduce load on your servers
- Database usually starts with vertical scaling, then moves to sharding

### ❌ Common Mistakes

- Keeping state in application servers (breaks horizontal scaling)
- Ignoring database scaling (bottleneck often happens there)
- Not testing auto-scaling behavior before launch

### 📝 Assignment 1

**Task:** You have a Django REST API serving 10,000 requests/minute. Single server has 70% CPU and 60% RAM.

1. What would you do first — vertical or horizontal scale? Why?
2. What changes are needed in the Django app to support horizontal scaling?
3. Draw an architecture diagram with 3 Django instances behind a load balancer
4. Where would you store user sessions?
5. How would you deploy the new instances without downtime?

---

## STEP 2: Database Scaling — Replication & Sharding

### 📖 Concept Explanation

As your app grows, your database becomes the bottleneck. Here's how to scale it.

### 📊 Database Replication

**Replication** means copying data from one database server (primary) to one or more others (replicas).

```
                [Primary DB]
                 /     |     \
                /      |      \
          [Replica 1] [Replica 2] [Replica 3]
```

**Read/Write Split:**
- ALL writes go to the Primary (ensures consistency)
- ALL reads go to Replicas (distributes read load)

**Use case:** 90% of typical app traffic is reads. This can dramatically reduce primary DB load.

```python
# Django Database Router for Read/Write Split
class ReadWriteRouter:
    def db_for_read(self, model, **hints):
        return 'replica'   # Reads go to replica

    def db_for_write(self, model, **hints):
        return 'primary'   # Writes go to primary
```

**Types of replication:**
- **Synchronous:** Primary waits for replica to confirm → no data loss, but slower
- **Asynchronous:** Primary doesn't wait → faster, but small risk of data loss if primary crashes

### 📊 Database Sharding

**Sharding** splits data across multiple databases so no single database holds all data.

```
Without Sharding:
[All 100M users in one DB] ← Slow, overloaded!

With Sharding (by user_id):
[Users 1-25M   → DB Shard 1]
[Users 25M-50M → DB Shard 2]
[Users 50M-75M → DB Shard 3]
[Users 75M-100M → DB Shard 4]
```

**Sharding Strategies:**

| Strategy | How | Pros | Cons |
|---------|-----|------|------|
| Range-based | user_id 1-1M → Shard 1 | Simple to understand | Uneven distribution (hotspots) |
| Hash-based | shard = hash(user_id) % 4 | Even distribution | Hard to add shards later |
| Geographic | Users in BD → Shard-Asia | Low latency for region | Cross-region queries are hard |
| Directory-based | Lookup table says which shard | Flexible | Lookup table is a bottleneck |

**Sharding Challenges:**
- Cross-shard queries are complex (JOINs across shards don't work)
- Re-sharding is painful
- Transactions across shards are tricky

### 🌍 Real-World Example

**Instagram's PostgreSQL sharding:**
- Started with one PostgreSQL database
- As they grew to billions of photos, they sharded by `user_id`
- All data for one user lives on one shard (so their feed queries don't need cross-shard joins)

**Cassandra/MongoDB:**
These NoSQL databases have built-in sharding (called "partitioning") that's automatic.

### ✅ Best Practices

- Start with replication, add sharding only when needed
- Choose your shard key carefully — it's hard to change later
- Keep related data on the same shard to avoid cross-shard queries
- Use a connection pooler (PgBouncer for PostgreSQL) to manage DB connections efficiently

### ❌ Common Mistakes

- Sharding too early (adds massive complexity)
- Bad shard key causing "hot shards" (one shard gets all traffic)
- Not handling shard rebalancing

### 📝 Assignment 2

**Task:** A social media app has 50 million users and 500 million posts.

1. Design a replication setup for the user database (how many replicas, sync or async, why?)
2. Design a sharding strategy for the posts table (what shard key and why?)
3. A user in Dhaka posts a new photo — trace the journey of that post through the sharded DB
4. A user wants to see all posts by people they follow — what problem does sharding create? How do you solve it?

---

## STEP 3: Caching — Redis Deep Dive

### 📖 Concept Explanation

**Redis** (Remote Dictionary Server) is the most popular in-memory data store. It's not just for caching — it's a full-featured data structure server.

**Why Redis?**
- Runs entirely in RAM (100x faster than disk-based databases)
- Supports many data structures: Strings, Lists, Sets, Sorted Sets, Hashes, Streams
- Built-in TTL (expiry) for cache
- Pub/Sub for real-time messaging
- Atomic operations

### 📊 Redis Data Structures & Use Cases

```
STRING
  COMMAND: SET user:1:name "Rahim"
  GET user:1:name → "Rahim"
  USE CASE: Session data, simple cache

HASH (like a dictionary)
  COMMAND: HSET user:1 name "Rahim" email "r@email.com" age 25
  HGET user:1 name → "Rahim"
  HGETALL user:1 → all fields
  USE CASE: User profile cache, product details

LIST (ordered, allows duplicates)
  COMMAND: RPUSH notifications:user1 "New follower" "New like"
  LRANGE notifications:user1 0 -1 → all items
  USE CASE: Activity feeds, queues, job queues

SET (unordered, unique values)
  COMMAND: SADD user:1:following 2 3 4 5
  SISMEMBER user:1:following 3 → 1 (yes)
  SINTERSTORE common user:1:following user:2:following
  USE CASE: Tags, unique visitors, follow/follower relationships

SORTED SET (set with score, ordered by score)
  COMMAND: ZADD leaderboard 1500 "PlayerA" 1200 "PlayerB" 1800 "PlayerC"
  ZRANGE leaderboard 0 -1 → ordered by score
  USE CASE: Leaderboards, trending content, rate limiting

STREAM (append-only log)
  USE CASE: Event sourcing, message queues, audit logs
```

### 🌍 Common Redis Patterns

**Pattern 1: Cache-Aside (Lazy Loading)**
```python
def get_product(product_id):
    # Try cache first
    cache_key = f"product:{product_id}"
    cached = redis.get(cache_key)
    
    if cached:
        return json.loads(cached)  # Cache HIT
    
    # Cache MISS - fetch from DB
    product = db.query("SELECT * FROM products WHERE id = %s", product_id)
    
    # Store in cache with 1 hour TTL
    redis.setex(cache_key, 3600, json.dumps(product))
    
    return product
```

**Pattern 2: Rate Limiting with Redis**
```python
def is_rate_limited(user_id, limit=100, window=60):
    """Allow max 100 requests per 60 seconds per user"""
    key = f"rate_limit:{user_id}:{int(time.time() / window)}"
    
    count = redis.incr(key)
    if count == 1:
        redis.expire(key, window)  # Set TTL only on first request
    
    return count > limit  # True means rate limited
```

**Pattern 3: Distributed Lock**
```python
def acquire_lock(resource, timeout=10):
    """Ensure only one instance processes a resource at a time"""
    lock_key = f"lock:{resource}"
    return redis.set(lock_key, "locked", nx=True, ex=timeout)
    # nx=True: only set if not exists
    # ex=timeout: auto-expire after timeout

def release_lock(resource):
    redis.delete(f"lock:{resource}")
```

**Pattern 4: Pub/Sub for Real-time**
```python
# Publisher (one service)
redis.publish("notifications", json.dumps({
    "user_id": 123,
    "message": "Your order has shipped!"
}))

# Subscriber (another service - WebSocket server)
pubsub = redis.pubsub()
pubsub.subscribe("notifications")
for message in pubsub.listen():
    data = json.loads(message['data'])
    # Push to user's WebSocket connection
```

### 📊 Cache Eviction Policies

When Redis memory is full, it needs to remove something. Policies:

| Policy | Behavior | Best For |
|--------|---------|---------|
| allkeys-lru | Remove least recently used | General caching |
| volatile-lru | Remove LRU among keys with TTL | Mix of cached and permanent |
| allkeys-lfu | Remove least frequently used | Hot/cold data patterns |
| allkeys-random | Remove random key | When access is random |
| noeviction | Return error when full | When losing data is not okay |

### ✅ Best Practices

- Always set TTLs (never cache forever)
- Use structured key naming: `entity:id:field` (e.g., `user:123:profile`)
- Monitor memory usage and hit rate
- Use Redis Cluster for horizontal scaling of Redis itself
- Use Redis Sentinel for automatic failover

### ❌ Common Mistakes

- Not setting eviction policy (OOM crash)
- Using Redis as primary database (data loss risk)
- Storing large objects (GBs) in Redis — it's RAM, it's expensive
- Not handling Redis connection failures gracefully

### 📝 Assignment 3

**Task:** Build a caching layer for a product catalog system:

1. Design the Redis key structure for: product details, product categories, product search results
2. Write pseudocode for:
   a. Fetching a product (cache-aside pattern)
   b. Updating a product (cache invalidation)
   c. Rate limiting the product search API
3. A flash sale starts — 100,000 users hit the product page at once. How does Redis help?
4. Which Redis data structure would you use to track which users have already viewed a product today? (No duplicates, fast lookup)

---

## STEP 4: Load Balancing Strategies (Deep Dive)

### 📖 Concept Explanation

We covered basic load balancing. Now let's go deeper.

**Layer 4 vs Layer 7 Load Balancing:**

| Type | Operates At | Knows About | Speed |
|------|------------|-------------|-------|
| L4 (Transport) | TCP/UDP level | IP, Port only | Very Fast |
| L7 (Application) | HTTP level | URLs, Headers, Cookies | Slightly slower, smarter |

**L7 Load Balancing enables:**
- Route `/api/` to backend servers
- Route `/static/` to CDN or static servers
- Route based on headers (A/B testing)
- SSL termination
- Request/response modification

### 📊 Nginx as L7 Load Balancer

```nginx
upstream api_servers {
    least_conn;  # Algorithm: least connections
    server 192.168.1.10:8000 weight=3;  # Gets 3x more traffic
    server 192.168.1.11:8000 weight=1;
    server 192.168.1.12:8000 backup;   # Only used if others fail
    
    keepalive 32;  # Persistent connections to backend
}

upstream static_servers {
    server 192.168.1.20:8080;
}

server {
    listen 443 ssl;
    server_name api.myapp.com;
    
    # SSL Termination here - backend servers use HTTP
    ssl_certificate /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;
    
    # Route API requests
    location /api/ {
        proxy_pass http://api_servers;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Host $http_host;
    }
    
    # Route static files differently
    location /static/ {
        proxy_pass http://static_servers;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "OK";
    }
}
```

### 📊 Health Checks

```nginx
upstream backend {
    server 192.168.1.10:8000;
    server 192.168.1.11:8000;
    
    # Active health check (nginx plus only)
    health_check interval=5s fails=3 passes=2;
}
```

**Passive health check (built-in nginx):**
```nginx
upstream backend {
    server 192.168.1.10:8000 max_fails=3 fail_timeout=30s;
    # After 3 failures, mark server as down for 30s
}
```

### 🌍 Sticky Sessions (Session Persistence)

Some apps need the same user to always hit the same server (e.g., long-running WebSocket connections).

```nginx
upstream backend {
    ip_hash;  # Same IP always goes to same server
    server 192.168.1.10:8000;
    server 192.168.1.11:8000;
}
```

**Better approach:** Make sessions stateless using Redis instead.

### ✅ Best Practices

- Always use health checks
- Use L7 load balancing for HTTP applications (smarter routing)
- SSL terminate at load balancer
- Set proper timeouts (read_timeout, connect_timeout)
- Log load balancer access logs for debugging

### ❌ Common Mistakes

- Not configuring health checks (dead servers still get traffic)
- Forgetting to pass real client IP to backend
- Not handling WebSocket upgrades in load balancer config

### 📝 Assignment 4

**Task:** Configure load balancing for a Django + Next.js app:

1. Design Nginx config that routes:
   - `/api/*` → Django backend (3 instances)
   - `/` → Next.js frontend (2 instances)
   - `/media/*` → Static file server
2. Which algorithm would you use for the Django backend? Why?
3. How would you configure health checks?
4. How would you implement rate limiting at the Nginx level?

---

## STEP 5: API Design Best Practices

### 📖 Concept Explanation

A well-designed API is a pleasure to use and easy to maintain. A poorly designed API is a nightmare for clients.

### 📊 RESTful API Design Principles

**1. Use nouns, not verbs in URLs:**
```
❌ Bad:
GET /getUser/123
POST /createPost
DELETE /deleteComment/456

✅ Good:
GET /users/123
POST /posts
DELETE /comments/456
```

**2. Use plural nouns:**
```
❌ GET /user/123
✅ GET /users/123
```

**3. Use HTTP methods properly:**
```
GET    /users          → List all users
POST   /users          → Create a user
GET    /users/123      → Get user 123
PUT    /users/123      → Replace user 123 entirely
PATCH  /users/123      → Update part of user 123
DELETE /users/123      → Delete user 123
```

**4. Nested resources:**
```
GET /users/123/posts         → Posts by user 123
GET /users/123/posts/456     → Specific post by user 123
POST /users/123/posts        → Create a post for user 123
```

**5. Filtering, Sorting, Pagination:**
```
GET /products?category=electronics&min_price=100&max_price=500
GET /products?sort=price&order=asc
GET /products?page=2&page_size=20
GET /products?search=iPhone
```

**6. Versioning:**
```
/api/v1/users   ← Version in URL (most common)
/api/v2/users   ← When breaking changes needed
```

### 📊 API Response Structure

**Success Response:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "name": "Rahim Ahmed",
    "email": "rahim@example.com"
  },
  "meta": {
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The provided email is invalid",
    "details": {
      "email": ["Enter a valid email address."]
    }
  }
}
```

**Paginated List Response:**
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "total": 1000,
    "page": 1,
    "page_size": 20,
    "next": "/api/v1/products?page=2",
    "previous": null
  }
}
```

### 📊 Django REST Framework Example

```python
# views.py
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']
    ordering = ['-created_at']  # Default ordering
    
    def get_queryset(self):
        # Scope to tenant/user if needed
        return Product.objects.filter(is_active=True).select_related('category')
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Custom action: POST /products/123/publish/"""
        product = self.get_object()
        product.is_published = True
        product.save()
        return Response({'status': 'published'})
    
    def destroy(self, request, *args, **kwargs):
        # Soft delete instead of hard delete
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
```

### ✅ Best Practices

- Always return consistent response structures
- Document your API (use Swagger/OpenAPI)
- Validate input and return clear error messages
- Use HTTPS always
- Return only the data the client needs (avoid over-fetching)
- Consider GraphQL if clients have very different data needs

### ❌ Common Mistakes

- Inconsistent response formats (sometimes data, sometimes nested, sometimes flat)
- Exposing internal implementation details in API responses
- Not versioning APIs (breaking clients when you change the API)
- Returning 200 for errors

### 📝 Assignment 5

**Task:** Design a complete RESTful API for a ride-sharing app (like Pathao/Uber):

1. Design endpoints for:
   - User registration and login
   - Request a ride
   - Track ride status
   - Driver availability update
   - Ride history

2. For each endpoint, specify: Method, URL, Request Body, Response

3. How would you handle real-time driver location updates? (Hint: WebSocket or polling)

4. Design the error response for "No drivers available"

---

## STEP 6: Rate Limiting

### 📖 Concept Explanation

**Rate Limiting** restricts how many requests a client can make in a given time window.

**Why it matters:**
- Prevents abuse and DDoS attacks
- Ensures fair usage across clients
- Protects your servers from being overwhelmed
- Prevents brute force attacks on login

**Types of Rate Limiting:**

| Type | Example |
|------|---------|
| Per user/IP | 100 requests/minute per user |
| Per API key | 1000 requests/hour per API key |
| Per endpoint | Login: 5 attempts/minute |
| Global | 10,000 requests/minute across all users |

### 📊 Rate Limiting Algorithms

**1. Fixed Window Counter:**
```
Window: 00:00 - 00:01 (60 seconds)
Limit: 100 requests

Count requests in window:
- Request 1-100: Allowed
- Request 101: BLOCKED (429 Too Many Requests)
- At 00:01: Counter resets
```
Problem: Burst at window boundary (100 at end of minute + 100 at start of next = 200 in 2 seconds)

**2. Sliding Window Log:**
```
Keep a log of timestamps of recent requests
For each request, check: how many requests in last 60 seconds?
More accurate but uses more memory
```

**3. Token Bucket:**
```
Bucket holds N tokens (max capacity)
Each request uses 1 token
Tokens are replenished at rate R per second

[🪣 Bucket: 10 tokens max, refill 2/sec]
Request comes in → use 1 token
No tokens → reject request

Allows bursting up to bucket capacity
Best for APIs where burst traffic is okay
```

**4. Leaky Bucket:**
```
Requests enter a queue (bucket)
Processed at a fixed rate (leaks out slowly)
If bucket is full, new requests are dropped

Best for smoothing traffic bursts
```

### 📊 Implementation in Django (with Redis)

```python
# Using django-ratelimit or custom Redis implementation

import time
import redis

r = redis.Redis()

def check_rate_limit(user_id: str, limit: int = 100, window: int = 60) -> bool:
    """
    Fixed window rate limiting.
    Returns True if request is allowed, False if rate limited.
    """
    current_window = int(time.time() / window)
    key = f"ratelimit:{user_id}:{current_window}"
    
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, window * 2)  # Keep for 2 windows
    results = pipe.execute()
    
    count = results[0]
    return count <= limit

# Django middleware
class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_id = request.user.id if request.user.is_authenticated else request.META.get('REMOTE_ADDR')
        
        if not check_rate_limit(str(user_id)):
            return JsonResponse(
                {'error': 'Rate limit exceeded. Try again later.'},
                status=429,
                headers={
                    'Retry-After': '60',
                    'X-RateLimit-Limit': '100',
                    'X-RateLimit-Remaining': '0'
                }
            )
        
        return self.get_response(request)
```

### ✅ Best Practices

- Return `429 Too Many Requests` when rate limited
- Include `Retry-After` header so clients know when to retry
- Include `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers
- Use different limits for different endpoints (login vs profile view)
- Consider using API gateway (Kong, AWS API Gateway) for rate limiting

### ❌ Common Mistakes

- Rate limiting by IP only (shared IPs in offices, universities)
- Same limit for all endpoints (login should be stricter than a product list)
- Not informing the client how long to wait

### 📝 Assignment 6

**Task:** Design rate limiting for a payment API:

1. What rate limits would you set for:
   a. POST /payments (create a payment)
   b. GET /payments/history
   c. POST /auth/login
2. Implement token bucket pseudocode for the payments endpoint
3. What happens if a legitimate user triggers the rate limit accidentally? How do you help them?

---

## STEP 7: Background Jobs — Celery & Task Queues

### 📖 Concept Explanation

Some tasks are too slow or too heavy to do during an HTTP request:
- Sending emails
- Generating PDF reports
- Processing images/videos
- Sending 10,000 push notifications
- Syncing with third-party APIs

**Solution:** Background jobs — offload heavy work to a separate process using a task queue.

**Stack:**
- **Celery:** Python task queue library (most popular for Django)
- **Redis or RabbitMQ:** The message broker (stores the task queue)
- **Flower:** Web dashboard for monitoring Celery tasks

### 📊 Celery Architecture

```
[Django Web Server]
       |
       | → task.delay()  (sends task to queue)
       v
[Redis/RabbitMQ Queue]
       |
       | → picks up task
       v
[Celery Worker Process]
       |
       | → processes task (send email, etc.)
       v
[Task result stored in Redis]
       |
[Django can check result later]
```

### 📊 Celery Implementation

```python
# celery.py
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myapp.settings')
app = Celery('myapp')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_EXPIRES = 3600  # Results expire in 1 hour

# tasks.py
from celery import shared_task
from django.core.mail import send_mail
import time

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_confirmation_email(self, order_id, user_email):
    """Send order confirmation email with retry logic."""
    try:
        order = Order.objects.get(id=order_id)
        send_mail(
            subject=f'Order #{order_id} Confirmed!',
            message=f'Your order for {order.total_amount} BDT is confirmed.',
            from_email='noreply@myapp.com',
            recipient_list=[user_email],
        )
        return {'status': 'sent', 'order_id': order_id}
    except Exception as exc:
        # Retry after 60 seconds, up to 3 times
        raise self.retry(exc=exc)

@shared_task
def generate_monthly_report(month, year):
    """Heavy report generation - runs in background."""
    # This could take minutes
    data = collect_sales_data(month, year)
    pdf = generate_pdf_report(data)
    upload_to_s3(pdf)
    notify_admin(f"Report for {month}/{year} ready!")

# views.py - triggering tasks
def place_order(request):
    order = Order.objects.create(...)
    
    # Fire and forget - don't wait for email!
    send_order_confirmation_email.delay(order.id, request.user.email)
    
    return Response({'order_id': order.id, 'status': 'confirmed'})

# Scheduled tasks with Celery Beat
# celery.py
app.conf.beat_schedule = {
    'generate-daily-report': {
        'task': 'myapp.tasks.generate_daily_report',
        'schedule': crontab(hour=0, minute=0),  # Every midnight
    },
    'cleanup-expired-sessions': {
        'task': 'myapp.tasks.cleanup_sessions',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
}
```

### 📊 Task Priorities and Routing

```python
# Route different tasks to different queues
app.conf.task_routes = {
    'myapp.tasks.send_email': {'queue': 'email'},
    'myapp.tasks.process_payment': {'queue': 'critical'},
    'myapp.tasks.generate_report': {'queue': 'low_priority'},
}

# Start workers for different queues
# $ celery -A myapp worker -Q critical --concurrency=8
# $ celery -A myapp worker -Q email --concurrency=4
# $ celery -A myapp worker -Q low_priority --concurrency=2
```

### ✅ Best Practices

- Always handle task failures with retries and exponential backoff
- Use task routing to separate critical and non-critical tasks
- Monitor task queue depth (growing queue = workers can't keep up)
- Set task timeouts (prevent zombie tasks running forever)
- Use idempotent tasks (safe to run twice without duplicate effects)

### ❌ Common Mistakes

- Running tasks synchronously when they should be async
- Not handling exceptions in tasks (tasks fail silently)
- Not monitoring queue depth
- Tasks that aren't idempotent (duplicate emails, duplicate charges)

### 📝 Assignment 7

**Task:** An e-learning platform needs to:
1. Email certificate when a course is completed
2. Generate a PDF certificate
3. Update learner's profile with completed courses
4. Notify instructor that student completed their course
5. Send analytics event to a tracking service

Design the Celery task architecture:
1. Which tasks need to run immediately? Which can be async?
2. Write Celery task signatures for each
3. Design a task chain (Task A runs, then B runs, then C)
4. What happens if the PDF generation task fails? Design retry logic.
5. How would you monitor if the email queue is backed up?

---

## STEP 8: Logging & Monitoring Basics

### 📖 Concept Explanation

In production, you can't attach a debugger. **Logging** is how you understand what's happening in your system. **Monitoring** is how you detect problems before users report them.

**Logging Levels (in order of severity):**
```
DEBUG    → Detailed info for debugging (disabled in production)
INFO     → General information (user logged in, order created)
WARNING  → Something unexpected but not breaking (retry attempt)
ERROR    → Something failed (payment failed, DB error)
CRITICAL → System is going down (DB unreachable, out of disk)
```

### 📊 Structured Logging in Django

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/app/django.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
        },
        'myapp': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        }
    }
}

# In your views/services
import logging

logger = logging.getLogger(__name__)

def process_payment(order_id, amount):
    logger.info("Processing payment", extra={
        "order_id": order_id,
        "amount": amount,
        "user_id": request.user.id
    })
    
    try:
        result = payment_gateway.charge(amount)
        logger.info("Payment successful", extra={
            "order_id": order_id,
            "transaction_id": result.transaction_id
        })
    except PaymentError as e:
        logger.error("Payment failed", extra={
            "order_id": order_id,
            "error": str(e),
            "error_code": e.code
        })
        raise
```

### 📊 Monitoring — Key Metrics to Track

**4 Golden Signals (Google SRE):**

| Signal | Description | Example Alert |
|--------|-------------|---------------|
| Latency | How long requests take | p95 > 500ms → alert |
| Traffic | Request volume | Sudden 10x spike → alert |
| Errors | Error rate | Error rate > 1% → alert |
| Saturation | Resource utilization | CPU > 85% for 5 min → alert |

**Tools:**

```
Logging Stack:
- Application → Logs → ELK Stack (Elasticsearch + Logstash + Kibana)
- Application → Logs → Loki + Grafana (lighter, newer)

Metrics Stack:
- Application → Prometheus metrics → Prometheus → Grafana dashboards

Error Tracking:
- Application → Sentry (instant error alerts with stack traces)

APM (Application Performance Monitoring):
- Datadog, New Relic, Elastic APM
```

### 📊 Prometheus + Grafana (Simple Setup)

```python
# Django with prometheus_client
from prometheus_client import Counter, Histogram, generate_latest
import time

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration', ['endpoint'])

class MetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.path,
            status=response.status_code
        ).inc()
        
        REQUEST_DURATION.labels(endpoint=request.path).observe(duration)
        
        return response
```

### ✅ Best Practices

- Log structured data (JSON) not plain strings — makes searching easier
- Include correlation/request IDs in every log — trace a request across services
- Don't log sensitive data (passwords, credit card numbers, tokens)
- Set up alerting (Grafana alerts, PagerDuty) not just dashboards
- Log at the right level (don't log everything as ERROR)

### ❌ Common Mistakes

- Not logging in production
- Logging sensitive data
- Only checking logs after something breaks (set up proactive alerts)
- Storing logs on the application server (fills up disk, lost if server dies)

### 📝 Assignment 8

**Task:** Set up a monitoring plan for a Django e-commerce app:

1. List 5 important metrics to track (beyond the 4 golden signals)
2. Write the logging configuration for a Django app
3. What would you alert on? Write 5 alert rules in plain English
4. A customer reports they couldn't checkout 30 minutes ago. How would you use logs to investigate?
5. Design a simple log format that includes: timestamp, request_id, user_id, endpoint, duration, status_code

---

## STEP 9: Introduction to Security

### 📖 Concept Explanation

Security is not optional. It's a core part of system design.

**Common web security threats:**

### 📊 1. SQL Injection

```python
# ❌ VULNERABLE — never do this!
username = request.GET['username']
query = f"SELECT * FROM users WHERE username = '{username}'"
# If username = "admin' OR '1'='1", the query becomes:
# SELECT * FROM users WHERE username = 'admin' OR '1'='1'
# Returns ALL users!

# ✅ SAFE — use parameterized queries (Django ORM handles this)
user = User.objects.get(username=username)  # Safe!
# Or with raw SQL:
cursor.execute("SELECT * FROM users WHERE username = %s", [username])
```

### 📊 2. Authentication & JWT

```python
# JWT (JSON Web Token) for stateless auth
# Header: {"alg": "HS256", "typ": "JWT"}
# Payload: {"user_id": 123, "exp": 1711900800}
# Signature: HMACSHA256(base64(header) + base64(payload), secret)

# In Django with SimpleJWT
from rest_framework_simplejwt.tokens import RefreshToken

def login(request):
    user = authenticate(request.data['username'], request.data['password'])
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),   # Short-lived (15 min)
            'refresh': str(refresh),                 # Long-lived (7 days)
        })

# Protecting an endpoint
from rest_framework.permissions import IsAuthenticated

class MyView(APIView):
    permission_classes = [IsAuthenticated]
    # Only authenticated users can access this
```

### 📊 3. CORS (Cross-Origin Resource Sharing)

```python
# settings.py - django-cors-headers
CORS_ALLOWED_ORIGINS = [
    "https://myapp.com",           # Only allow your frontend
    "https://www.myapp.com",
]
# NOT: CORS_ALLOW_ALL_ORIGINS = True  ← dangerous in production!
```

### 📊 4. Input Validation

```python
# Always validate and sanitize inputs
from rest_framework import serializers

class OrderSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(min_value=1, max_value=100)
    product_id = serializers.IntegerField(min_value=1)
    
    def validate_quantity(self, value):
        if value > 50:
            raise serializers.ValidationError("Maximum 50 items per order")
        return value
```

### 📊 5. Security Checklist for Production

```
Authentication:
  ✅ Use HTTPS everywhere
  ✅ Hash passwords with bcrypt (Django does this by default)
  ✅ JWT tokens with short expiry (15 min for access token)
  ✅ Implement refresh token rotation
  ✅ Rate limit login attempts

Data Protection:
  ✅ Encrypt sensitive data at rest
  ✅ Never log passwords, tokens, credit cards
  ✅ Use environment variables for secrets (not hardcoded)
  ✅ .env files never committed to git

API Security:
  ✅ Validate all inputs
  ✅ Use parameterized queries (prevent SQL injection)
  ✅ Set Content Security Policy headers
  ✅ Enable CORS with specific allowed origins
  ✅ Set rate limits

Infrastructure:
  ✅ Keep dependencies updated
  ✅ Run with minimal permissions
  ✅ Use secrets manager (AWS Secrets Manager, Vault)
```

### ✅ Best Practices

- Follow the principle of least privilege (users/services only get permissions they need)
- Use OWASP Top 10 as a security checklist
- Run automated security scans in CI/CD (Bandit for Python, Snyk for dependencies)
- Have a security incident response plan

### ❌ Common Mistakes

- Hardcoding secrets in source code (→ git history = leaked secrets)
- Using HTTP in production
- Not rotating credentials (API keys, DB passwords)
- CORS allow all origins in production

### 📝 Assignment 9

**Task:** Security audit for a Django REST API:

1. Review the following code and identify security vulnerabilities:
```python
def get_user_data(request):
    user_id = request.GET.get('id')
    query = f"SELECT * FROM users WHERE id = {user_id}"
    user = db.execute(query).fetchone()
    return JsonResponse({'password': user['password'], 'data': user})

SECRET_KEY = "myapp-secret-key-123"
DATABASE_URL = "postgresql://admin:password123@db.myapp.com/prod"
```

2. Fix all the vulnerabilities you found
3. What HTTP security headers should you add?
4. Design the authentication flow for a mobile app (registration → login → token refresh)

---

## STEP 10: Additional Intermediate Topics

### 📊 CDN (Content Delivery Network)

A CDN is a geographically distributed network of servers that delivers content to users from the nearest location.

```
Without CDN:
User in Dhaka → Server in Virginia, USA = High latency (200ms+)

With CDN:
User in Dhaka → CDN node in Singapore = Low latency (20ms)
                                        (Content cached from Virginia)
```

**What to put on CDN:**
- Images, videos, audio
- CSS, JavaScript bundles
- Static HTML pages
- Downloadable files

**Popular CDNs:** Cloudflare, AWS CloudFront, Fastly, Akamai

### 📊 API Gateway

An API Gateway is a single entry point for all client-side API requests:

```
Clients → [API Gateway] → [Auth Service]
                        → [User Service]
                        → [Product Service]
                        → [Order Service]

API Gateway handles:
- Authentication (validate JWT before forwarding)
- Rate limiting
- Request routing
- SSL termination
- Request/response transformation
- Logging
```

**Popular API Gateways:** Kong, AWS API Gateway, Nginx, Traefik

### 📝 Intermediate Capstone Assignment

**Task:** Design the complete backend architecture for a food delivery app with:
- 100,000 daily active users
- 500 orders per minute at peak

Your design must include:
1. API design for: user auth, restaurant listing, menu browsing, order placement, order tracking
2. Database design with proper indexing
3. Caching strategy (what to cache, TTLs, Redis data structures)
4. Background jobs (what tasks run async)
5. Load balancing setup
6. Rate limiting rules
7. Monitoring metrics to track
8. Basic security checklist

**Deliverable:** A written design document with ASCII architecture diagram.

---

## 🏁 Intermediate Level Complete!

**Concepts mastered:**
- ✅ Horizontal vs Vertical Scaling (with stateless design)
- ✅ Database Replication and Sharding
- ✅ Redis (deep dive, all patterns)
- ✅ Load Balancing Strategies (L4 vs L7, algorithms)
- ✅ API Design Best Practices (REST, versioning, pagination)
- ✅ Rate Limiting (algorithms, implementation)
- ✅ Background Jobs (Celery, patterns, monitoring)
- ✅ Logging & Monitoring (structured logs, metrics, alerting)
- ✅ Security (JWT, SQL injection, CORS, checklist)
- ✅ CDN and API Gateway basics

**Before moving to Advanced, ensure you can:**
- [ ] Design a stateless, horizontally scalable Django backend
- [ ] Choose the right caching strategy for different use cases
- [ ] Design and implement proper rate limiting
- [ ] Set up background tasks with proper retry/error handling
- [ ] Build a basic monitoring plan for a production system
- [ ] Identify and fix common security vulnerabilities

**➡️ Next: README_ADVANCED.md**
