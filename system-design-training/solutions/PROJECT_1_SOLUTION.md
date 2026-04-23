# 🔗 PROJECT 1 SOLUTION: SnapLink — Scalable URL Shortener

---

## 📐 System Design Explanation

### Core Requirements Analysis

**Write path:** User submits long URL → get back short URL
- Expected: ~100 URL creations/second at peak

**Read path:** User clicks short URL → redirected to long URL
- Expected: ~10,000 redirects/second at peak
- Read:Write ratio = 100:1

**This is a read-heavy system.** Our entire design must optimize for fast redirects.

---

## 🏗️ Architecture

```
                    WRITE PATH (URL Creation)
                    ─────────────────────────
[Client] ──HTTPS──→ [Nginx Load Balancer]
                         │
                         ▼
                    [Django API] (3 instances)
                         │
                    [PostgreSQL Primary]
                         │
                    [PostgreSQL Replica ×2]


                    READ PATH (Redirect) — Most Important!
                    ───────────────────────────────────────
[Browser] ──GET /{code}──→ [Nginx]
                                │
                                ▼
                         [Redirect Service]
                                │
                      ┌─────────┴─────────┐
                      ▼                   ▼
               [Redis Cache]         [PostgreSQL]
               (L1: 10ms)           (L2: fallback)
                      │
                      ▼ (async, non-blocking)
               [Analytics Queue]
                      │
                      ▼
               [Celery Worker]
                      │
                      ▼
               [Analytics DB]


                    BACKGROUND
                    ──────────
               [Celery Beat]
               ├── Cleanup expired URLs (daily)
               └── Aggregate analytics (hourly)
```

---

## 🗄️ Database Design

### PostgreSQL Schema

```sql
-- Users table
CREATE TABLE users (
    id          BIGSERIAL PRIMARY KEY,
    email       VARCHAR(255) UNIQUE NOT NULL,
    password    VARCHAR(255) NOT NULL,           -- bcrypt hashed
    api_key     UUID DEFAULT gen_random_uuid(),   -- for API access
    plan        VARCHAR(20) DEFAULT 'free',        -- free, pro, enterprise
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_api_key ON users(api_key);

-- URL mappings table (the core table)
CREATE TABLE urls (
    id           BIGSERIAL PRIMARY KEY,
    short_code   VARCHAR(12) UNIQUE NOT NULL,     -- our 7-char code
    long_url     TEXT NOT NULL,
    user_id      BIGINT REFERENCES users(id) ON DELETE SET NULL,
    custom_alias VARCHAR(50) UNIQUE,              -- optional custom slug
    title        VARCHAR(500),                    -- page title (fetched async)
    is_active    BOOLEAN DEFAULT TRUE,
    password     VARCHAR(255),                    -- optional password protection
    expires_at   TIMESTAMPTZ,                     -- optional expiry
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_urls_short_code ON urls(short_code);
CREATE INDEX idx_urls_user_id ON urls(user_id);
CREATE INDEX idx_urls_created_at ON urls(created_at);
-- Partial index: only active, non-expired URLs (most lookups)
CREATE INDEX idx_urls_active ON urls(short_code)
    WHERE is_active = TRUE AND (expires_at IS NULL OR expires_at > NOW());

-- Analytics table (append-only, partitioned by month)
CREATE TABLE clicks (
    id           BIGSERIAL,
    url_id       BIGINT NOT NULL REFERENCES urls(id),
    clicked_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ip_hash      VARCHAR(64),                     -- hashed IP (privacy)
    country      VARCHAR(2),                      -- ISO country code
    city         VARCHAR(100),
    device_type  VARCHAR(20),                     -- mobile, desktop, tablet, bot
    os           VARCHAR(50),
    browser      VARCHAR(50),
    referrer     VARCHAR(500),
    user_agent   TEXT
) PARTITION BY RANGE (clicked_at);

-- Create monthly partitions
CREATE TABLE clicks_2024_01 PARTITION OF clicks
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
-- (Create future partitions automatically with pg_partman)

-- Aggregated analytics (pre-computed for dashboard performance)
CREATE TABLE url_analytics_daily (
    url_id       BIGINT REFERENCES urls(id),
    date         DATE,
    total_clicks BIGINT DEFAULT 0,
    unique_clicks BIGINT DEFAULT 0,
    PRIMARY KEY (url_id, date)
);
```

### Why Partitioned Clicks Table?

With 10,000 redirects/second, we generate 864 million click records per day.
- Partitioning by month keeps each partition manageable
- Old partitions can be archived or dropped
- Queries for "last 30 days" only scan 1-2 partitions

---

## 🔑 URL Code Generation Algorithm

### Approach: Auto-Increment ID + Base62 Encoding

```python
# base62.py
import string

CHARS = string.digits + string.ascii_lowercase + string.ascii_uppercase
# "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
# 62 characters

def encode(num: int) -> str:
    """Convert integer to Base62 string."""
    if num == 0:
        return CHARS[0]
    result = []
    while num:
        result.append(CHARS[num % 62])
        num //= 62
    return ''.join(reversed(result))

def decode(code: str) -> int:
    """Convert Base62 string back to integer."""
    num = 0
    for char in code:
        num = num * 62 + CHARS.index(char)
    return num

# Examples:
# encode(1)        → "1"
# encode(62)       → "10"
# encode(1000000)  → "4c92"
# encode(3521614606207) → "zzzzzzzz" (8 chars, handles billions)
```

**Why Base62?**
- DB auto-increment ID guarantees uniqueness (no collision checking!)
- Short: ID 1,000,000 → 4 characters. ID 56,800,235,584 → 7 characters
- URL-safe: No special characters (`+`, `/`, `=` in Base64 are URL-unfriendly)

### Custom Alias Validation

```python
import re

RESERVED_WORDS = {'api', 'admin', 'static', 'health', 'login', 'register'}

def validate_alias(alias: str) -> str:
    alias = alias.lower().strip()
    if len(alias) < 3 or len(alias) > 50:
        raise ValueError("Alias must be 3-50 characters")
    if not re.match(r'^[a-z0-9-_]+$', alias):
        raise ValueError("Only lowercase letters, numbers, hyphens and underscores allowed")
    if alias in RESERVED_WORDS:
        raise ValueError("This alias is reserved")
    return alias
```

---

## ⚡ Caching Strategy

### Redis Key Design

```
Key: url:{short_code}
Value: JSON string of URL data
TTL: 24 hours (renewable on access)

Example:
Key: "url:abc123x"
Value: '{"long_url": "https://very-long-url.com/path", "is_active": true, "expires_at": null}'
TTL: 86400 seconds
```

### Cache-Aside Pattern for Redirects

```python
# services/redirect.py
import json
import redis
from django.core.cache import cache

r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

def get_url_for_redirect(short_code: str) -> dict | None:
    """
    Optimized URL lookup with cache-aside pattern.
    This is called on EVERY redirect — must be fast.
    """
    cache_key = f"url:{short_code}"
    
    # Step 1: Redis lookup (< 1ms)
    cached = r.get(cache_key)
    if cached:
        data = json.loads(cached)
        if data.get('not_found'):
            return None  # Negative cache (prevent DB spam for invalid codes)
        return data
    
    # Step 2: DB lookup (10-50ms)
    try:
        url = URL.objects.select_related().get(
            short_code=short_code,
            is_active=True
        )
    except URL.DoesNotExist:
        # Cache negative result (prevent repeated DB hits for invalid codes)
        r.setex(cache_key, 300, json.dumps({'not_found': True}))  # 5 min TTL
        return None
    
    # Check expiry
    if url.expires_at and url.expires_at < timezone.now():
        r.setex(cache_key, 300, json.dumps({'not_found': True, 'expired': True}))
        return None
    
    data = {
        'id': url.id,
        'long_url': url.long_url,
        'is_active': url.is_active,
        'user_id': url.user_id
    }
    
    # Cache for 24 hours
    r.setex(cache_key, 86400, json.dumps(data))
    
    return data


def record_click_async(url_id: int, request_data: dict):
    """
    Fire-and-forget analytics recording.
    Does NOT block the redirect response.
    """
    from apps.analytics.tasks import record_click
    record_click.delay(url_id, request_data)
```

### Cache Invalidation

```python
def invalidate_url_cache(short_code: str):
    """Called whenever a URL is updated or deleted."""
    r.delete(f"url:{short_code}")
```

---

## 🔄 Analytics Pipeline

### Async Click Recording (Non-blocking)

```python
# apps/analytics/tasks.py
from celery import shared_task
from user_agents import parse

@shared_task(queue='analytics', ignore_result=True)
def record_click(url_id: int, request_data: dict):
    """
    Runs in background Celery worker.
    Never blocks the redirect.
    """
    import geoip2.database
    
    ip = request_data.get('ip')
    user_agent_str = request_data.get('user_agent', '')
    
    # Parse user agent
    ua = parse(user_agent_str)
    
    # Geo lookup
    country, city = None, None
    if ip and not ip.startswith(('10.', '172.', '192.168.')):
        try:
            with geoip2.database.Reader('/var/lib/geoip/GeoLite2-City.mmdb') as reader:
                response = reader.city(ip)
                country = response.country.iso_code
                city = response.city.name
        except Exception:
            pass
    
    # Hash IP for privacy
    ip_hash = hashlib.sha256(ip.encode()).hexdigest() if ip else None
    
    Click.objects.create(
        url_id=url_id,
        ip_hash=ip_hash,
        country=country,
        city=city,
        device_type='mobile' if ua.is_mobile else 'tablet' if ua.is_tablet else 'desktop',
        os=ua.os.family,
        browser=ua.browser.family,
        referrer=request_data.get('referrer', '')[:500],
        user_agent=user_agent_str[:500]
    )


@shared_task(queue='analytics')
def aggregate_daily_analytics():
    """Run via Celery Beat every hour — pre-compute analytics for dashboard."""
    yesterday = date.today() - timedelta(days=1)
    
    # Aggregate yesterday's clicks per URL
    results = Click.objects.filter(
        clicked_at__date=yesterday
    ).values('url_id').annotate(
        total=Count('id'),
        unique=Count('ip_hash', distinct=True)
    )
    
    for result in results:
        URLAnalyticsDaily.objects.update_or_create(
            url_id=result['url_id'],
            date=yesterday,
            defaults={
                'total_clicks': result['total'],
                'unique_clicks': result['unique']
            }
        )
```

---

## 🛡️ Rate Limiting

```python
# shared/rate_limiting.py
import time
import redis

r = redis.Redis.from_url(settings.REDIS_URL)

def check_rate_limit(identifier: str, limit: int, window: int) -> tuple[bool, int]:
    """
    Sliding window rate limiter.
    Returns (is_allowed, remaining_requests)
    """
    now = time.time()
    window_start = now - window
    key = f"ratelimit:{identifier}"
    
    pipe = r.pipeline()
    # Remove old entries outside window
    pipe.zremrangebyscore(key, 0, window_start)
    # Count requests in current window
    pipe.zcard(key)
    # Add current request
    pipe.zadd(key, {str(now): now})
    # Set expiry
    pipe.expire(key, window)
    results = pipe.execute()
    
    count = results[1]  # Count before adding current request
    remaining = max(0, limit - count - 1)
    
    return count < limit, remaining


# In view
class URLCreateView(CreateAPIView):
    def create(self, request, *args, **kwargs):
        # Rate limit: authenticated users get 100/min, anonymous get 10/min
        if request.user.is_authenticated:
            identifier = f"user:{request.user.id}"
            limit, window = 100, 60
        else:
            identifier = f"ip:{request.META.get('REMOTE_ADDR')}"
            limit, window = 10, 60
        
        allowed, remaining = check_rate_limit(identifier, limit, window)
        
        if not allowed:
            return Response(
                {'error': 'Rate limit exceeded'},
                status=429,
                headers={
                    'X-RateLimit-Limit': str(limit),
                    'X-RateLimit-Remaining': '0',
                    'Retry-After': '60'
                }
            )
        
        response = super().create(request, *args, **kwargs)
        response['X-RateLimit-Remaining'] = str(remaining)
        return response
```

---

## 🔐 API Structure

### Views

```python
# apps/urls/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly

class URLShortenerView(generics.CreateAPIView):
    """
    POST /api/v1/urls/
    Create a short URL
    """
    serializer_class = URLCreateSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        long_url = serializer.validated_data['long_url']
        custom_alias = serializer.validated_data.get('custom_alias')
        expires_in_days = serializer.validated_data.get('expires_in_days')
        
        # Generate short code
        with transaction.atomic():
            url = URL.objects.create(
                long_url=long_url,
                user=request.user if request.user.is_authenticated else None,
                custom_alias=custom_alias,
                expires_at=timezone.now() + timedelta(days=expires_in_days) if expires_in_days else None
            )
            # Use DB ID for Base62 encoding
            url.short_code = custom_alias or base62.encode(url.id)
            url.save(update_fields=['short_code'])
        
        # Fetch page title asynchronously
        fetch_page_title.delay(url.id, long_url)
        
        return Response({
            'short_url': f"https://snap.lk/{url.short_code}",
            'short_code': url.short_code,
            'long_url': long_url,
            'created_at': url.created_at,
            'expires_at': url.expires_at,
        }, status=status.HTTP_201_CREATED)


class RedirectView(View):
    """
    GET /{short_code}
    This is the hot path — called millions of times
    Must be as fast as possible
    """
    def get(self, request, short_code):
        url_data = get_url_for_redirect(short_code)
        
        if not url_data:
            return render(request, '404.html', status=404)
        
        # Record click asynchronously (non-blocking)
        record_click_async(url_data['id'], {
            'ip': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referrer': request.META.get('HTTP_REFERER', ''),
        })
        
        return HttpResponseRedirect(url_data['long_url'])
```

---

## 📈 Scaling Strategy

### Current Scale: 10,000 redirects/second

```
Component       Count   Role
─────────────────────────────────────────────
Nginx           2       Load balancer (HA pair)
Django API      3       URL creation API
Redirect Svc    5       High-throughput redirect (stateless)
Redis           3       Cluster (1 primary, 2 replicas)
PostgreSQL      3       1 primary + 2 replicas (read scaling)
Celery Worker   3       Analytics processing
```

**Cache hit rate target: 90%+**
At 90% hit rate:
- 9,000 redirects/second served from Redis (< 1ms)
- 1,000 redirects/second hit PostgreSQL (< 50ms)
PostgreSQL can handle 1,000 reads/second comfortably.

### Future Scale: 100,000 redirects/second

Options:
1. **Cloudflare Workers:** Run redirect logic at the edge (150+ global PoPs) — sub-millisecond redirects
2. **Redis Cluster:** Shard Redis across 6 nodes
3. **Database sharding:** Shard URLs by short_code prefix

---

## ❌ Failure Handling

### Scenario 1: Redis is down

```python
def get_url_for_redirect(short_code: str) -> dict | None:
    try:
        cached = r.get(f"url:{short_code}")
        if cached:
            return json.loads(cached)
    except redis.RedisError:
        # Redis is down — fall through to DB
        logger.warning(f"Redis unavailable for redirect lookup: {short_code}")
    
    # Always have DB as fallback
    try:
        url = URL.objects.get(short_code=short_code, is_active=True)
        return {'long_url': url.long_url, 'id': url.id}
    except URL.DoesNotExist:
        return None
```

### Scenario 2: Database primary is down

- PostgreSQL Replica automatically promoted by Patroni
- Typical failover: 30-60 seconds
- During failover: Redis cache handles most reads (90% hit rate)
- Write operations (URL creation): Temporarily return 503 with Retry-After header

### Scenario 3: Analytics queue backup

```python
@shared_task(queue='analytics', max_retries=5, default_retry_delay=60)
def record_click(url_id, request_data):
    try:
        # ... process click
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

Analytics data loss is acceptable (redirect is the critical path). We use a dead-letter queue to investigate failures without blocking new clicks.

---

## ⚖️ Trade-offs

| Decision | Trade-off |
|----------|----------|
| Base62 + auto-increment | Predictable (attackers can guess codes) vs. simple and no collision |
| Cache-aside pattern | Cache miss causes DB hit, but simple to implement correctly |
| Async analytics | Slightly delayed stats vs. zero impact on redirect speed |
| Partitioned clicks table | More complex setup vs. dramatically better query performance |
| Redis cache TTL: 24h | Stale data risk if URL is deleted vs. high cache efficiency |

**On predictable codes:**
Sequential IDs mean codes are predictable (abc123x, abc123y). For most URL shorteners this is fine. If privacy is required, use random codes with collision detection.
