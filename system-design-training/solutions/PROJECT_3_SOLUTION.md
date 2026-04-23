# 🛒 PROJECT 3 SOLUTION: MarketFlow — High-Traffic E-Commerce Order Processing

---

## 📐 System Design Explanation

### Core Challenges

1. **No overselling:** Two users cannot buy the last item simultaneously
2. **Flash sale traffic:** 10x normal load (1M orders/day spike)
3. **Order atomicity:** Inventory deduction + payment + order creation must succeed or all rollback
4. **Performance:** Product pages < 200ms, checkout < 500ms

---

## 🏗️ Architecture

```
                    ┌──────────────────────────────────────────────────┐
                    │                  MarketFlow                       │
                    └──────────────────────────────────────────────────┘

[Web / Mobile Client]
         │
         ▼
[Nginx Load Balancer + Rate Limiter]
         │
         ├──→ /api/products/*  ──→ [Django API — Product Service]
         │                              │
         │                        [Elasticsearch] [Redis Cache]
         │                              
         ├──→ /api/cart/*      ──→ [Django API — Cart Service]
         │                              │
         │                           [Redis] (cart data)
         │
         ├──→ /api/orders/*    ──→ [Django API — Order Service]
         │                              │
         │                       [PostgreSQL Primary]
         │                       [PostgreSQL Replica]
         │
         └──→ /api/payments/*  ──→ [Django API — Payment Service]
                                       │
                               [Stripe/Payment Gateway]

[Celery Workers]
    ├── Queue: critical   → Payment webhooks, inventory sync
    ├── Queue: email      → Order confirmations, shipping updates
    ├── Queue: sms        → SMS notifications
    └── Queue: analytics  → Event tracking

[Redis]
    ├── Cart storage
    ├── Flash sale inventory counters
    ├── Product cache
    └── Rate limiting

[S3 + CloudFront] → Product images
[Admin Django] → Seller dashboard, inventory management
```

---

## 🗄️ Database Design

```sql
-- Categories
CREATE TABLE categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    slug        VARCHAR(100) UNIQUE NOT NULL,
    parent_id   INT REFERENCES categories(id),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Sellers
CREATE TABLE sellers (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT REFERENCES users(id),
    shop_name   VARCHAR(200) NOT NULL,
    rating      DECIMAL(3,2) DEFAULT 0,
    total_sales BIGINT DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Products
CREATE TABLE products (
    id            BIGSERIAL PRIMARY KEY,
    seller_id     BIGINT NOT NULL REFERENCES sellers(id),
    category_id   INT NOT NULL REFERENCES categories(id),
    name          VARCHAR(500) NOT NULL,
    slug          VARCHAR(500) UNIQUE NOT NULL,
    description   TEXT,
    price         NUMERIC(10,2) NOT NULL,
    compare_price NUMERIC(10,2),            -- Original price (for discounts)
    sku           VARCHAR(100) UNIQUE,
    weight_kg     DECIMAL(6,3),
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_seller ON products(seller_id);
CREATE INDEX idx_products_active ON products(is_active, created_at DESC);

-- Inventory (separate table for clear ownership and locking)
CREATE TABLE inventory (
    product_id    BIGINT PRIMARY KEY REFERENCES products(id),
    quantity      INT NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    reserved      INT NOT NULL DEFAULT 0 CHECK (reserved >= 0),
    -- available = quantity - reserved
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Product Images
CREATE TABLE product_images (
    id          BIGSERIAL PRIMARY KEY,
    product_id  BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    url         TEXT NOT NULL,
    thumbnail   TEXT,
    is_primary  BOOLEAN DEFAULT FALSE,
    position    SMALLINT DEFAULT 0
);

-- Product Variants (size, color, etc.)
CREATE TABLE product_variants (
    id          BIGSERIAL PRIMARY KEY,
    product_id  BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    name        VARCHAR(100) NOT NULL,   -- "Red / XL"
    sku         VARCHAR(100) UNIQUE,
    price_diff  NUMERIC(10,2) DEFAULT 0, -- additional cost vs base price
    stock       INT DEFAULT 0
);

-- Addresses
CREATE TABLE addresses (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id),
    full_name   VARCHAR(200) NOT NULL,
    phone       VARCHAR(20) NOT NULL,
    address_line1 TEXT NOT NULL,
    city        VARCHAR(100) NOT NULL,
    district    VARCHAR(100),
    country     VARCHAR(2) DEFAULT 'BD',
    is_default  BOOLEAN DEFAULT FALSE
);

-- Orders
CREATE TABLE orders (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id),
    status          VARCHAR(30) NOT NULL DEFAULT 'pending',
    -- pending → paid → processing → shipped → delivered → completed
    -- OR: pending → cancelled | paid → refund_requested → refunded
    
    subtotal        NUMERIC(12,2) NOT NULL,
    shipping_cost   NUMERIC(10,2) DEFAULT 0,
    discount        NUMERIC(10,2) DEFAULT 0,
    total_amount    NUMERIC(12,2) NOT NULL,
    
    shipping_address JSONB NOT NULL,     -- Snapshot of address at order time
    payment_method  VARCHAR(50),
    payment_ref     VARCHAR(200),        -- External payment reference
    
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    paid_at         TIMESTAMPTZ,
    shipped_at      TIMESTAMPTZ,
    delivered_at    TIMESTAMPTZ
) PARTITION BY RANGE (created_at);

CREATE INDEX idx_orders_user ON orders(user_id, created_at DESC);
CREATE INDEX idx_orders_status ON orders(status);

-- Order Items
CREATE TABLE order_items (
    id          BIGSERIAL PRIMARY KEY,
    order_id    BIGINT NOT NULL REFERENCES orders(id),
    product_id  BIGINT NOT NULL REFERENCES products(id),
    variant_id  BIGINT REFERENCES product_variants(id),
    quantity    INT NOT NULL,
    unit_price  NUMERIC(10,2) NOT NULL,   -- Price snapshot at order time
    product_snapshot JSONB NOT NULL        -- Full product snapshot (name, image, etc.)
);

CREATE INDEX idx_order_items_order ON order_items(order_id);

-- Flash Sales
CREATE TABLE flash_sales (
    id              SERIAL PRIMARY KEY,
    product_id      BIGINT NOT NULL REFERENCES products(id),
    flash_price     NUMERIC(10,2) NOT NULL,
    available_stock INT NOT NULL,
    starts_at       TIMESTAMPTZ NOT NULL,
    ends_at         TIMESTAMPTZ NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE
);
```

---

## 🛒 Cart Design (Redis)

**Why Redis for cart?**
- Cart changes frequently (add/remove/update)
- Doesn't need ACID guarantees
- Needs to be fast (user is actively shopping)
- Expires naturally (7 days TTL)

```python
# apps/cart/service.py
import json
import redis

r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

class CartService:
    CART_TTL = 7 * 24 * 3600  # 7 days in seconds
    
    def get_cart_key(self, user_id: int) -> str:
        return f"cart:user:{user_id}"
    
    def get_cart(self, user_id: int) -> dict:
        """
        Cart stored as Redis Hash:
        Key: cart:user:123
        Fields: product:{product_id} → JSON (quantity, price, name, image)
        """
        cart_key = self.get_cart_key(user_id)
        raw_items = r.hgetall(cart_key)
        
        items = {}
        for field, value in raw_items.items():
            product_id = field.split(':')[1]
            items[product_id] = json.loads(value)
        
        return {
            'items': items,
            'total': sum(item['price'] * item['quantity'] for item in items.values())
        }
    
    def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1) -> dict:
        cart_key = self.get_cart_key(user_id)
        field = f"product:{product_id}"
        
        # Get product data
        product = Product.objects.select_related().get(id=product_id, is_active=True)
        
        # Check stock availability
        inv = product.inventory
        if inv.quantity - inv.reserved < quantity:
            raise ValueError("Insufficient stock")
        
        # Get existing quantity in cart (if any)
        existing = r.hget(cart_key, field)
        existing_qty = json.loads(existing)['quantity'] if existing else 0
        new_qty = existing_qty + quantity
        
        item_data = {
            'product_id': product_id,
            'quantity': new_qty,
            'price': float(product.price),
            'name': product.name,
            'image': product.primary_image_url,
            'max_stock': inv.quantity - inv.reserved
        }
        
        pipe = r.pipeline()
        pipe.hset(cart_key, field, json.dumps(item_data))
        pipe.expire(cart_key, self.CART_TTL)  # Reset TTL on activity
        pipe.execute()
        
        return item_data
    
    def remove_from_cart(self, user_id: int, product_id: int):
        cart_key = self.get_cart_key(user_id)
        r.hdel(cart_key, f"product:{product_id}")
    
    def clear_cart(self, user_id: int):
        r.delete(self.get_cart_key(user_id))
    
    def get_cart_count(self, user_id: int) -> int:
        """Total items in cart (fast)."""
        return r.hlen(self.get_cart_key(user_id))
```

---

## ⚡ Inventory Management — Preventing Overselling

This is the most critical part of the system.

### The Problem

```
Product has 1 unit left.
User A and User B both see "1 in stock" and click "Add to Cart" simultaneously.

Without proper handling:
Thread 1: SELECT quantity (= 1) → OK, proceed
Thread 2: SELECT quantity (= 1) → OK, proceed
Thread 1: UPDATE SET quantity = 0 → Done
Thread 2: UPDATE SET quantity = 0 → Done, but we sold twice!
```

### Solution: PostgreSQL SELECT FOR UPDATE

```python
# apps/orders/services.py
from django.db import transaction

class OrderService:
    
    def place_order(self, user_id: int, cart_items: list, address_id: int) -> Order:
        """
        Atomic order placement.
        All inventory is reserved and order is created in one transaction.
        """
        with transaction.atomic():
            order = self._create_order_from_cart(user_id, cart_items, address_id)
            return order
    
    def _create_order_from_cart(self, user_id, cart_items, address_id):
        # Step 1: Lock inventory rows FOR UPDATE
        # This prevents any other transaction from modifying these rows
        # until our transaction is complete
        product_ids = [item['product_id'] for item in cart_items]
        
        inventories = Inventory.objects.select_for_update().filter(
            product_id__in=product_ids
        ).in_bulk(field_name='product_id')
        # SELECT ... FOR UPDATE: Row-level lock acquired!
        
        # Step 2: Validate and calculate
        order_items_data = []
        subtotal = Decimal('0')
        
        for item in cart_items:
            inv = inventories.get(item['product_id'])
            if not inv:
                raise ValueError(f"Product {item['product_id']} not found")
            
            available = inv.quantity - inv.reserved
            if available < item['quantity']:
                raise InsufficientStockError(
                    f"Only {available} units available for product {item['product_id']}"
                )
            
            product = inv.product
            unit_price = product.price
            
            order_items_data.append({
                'product_id': item['product_id'],
                'quantity': item['quantity'],
                'unit_price': unit_price,
                'product_snapshot': {
                    'name': product.name,
                    'image': product.primary_image_url,
                    'sku': product.sku
                }
            })
            
            subtotal += unit_price * item['quantity']
        
        # Step 3: Create the order
        address = Address.objects.get(id=address_id, user_id=user_id)
        
        order = Order.objects.create(
            user_id=user_id,
            status='pending',
            subtotal=subtotal,
            shipping_cost=Decimal('60'),  # Flat rate
            total_amount=subtotal + Decimal('60'),
            shipping_address={
                'full_name': address.full_name,
                'phone': address.phone,
                'address': address.address_line1,
                'city': address.city,
            }
        )
        
        # Step 4: Create order items + reserve inventory
        order_items = []
        for item_data in order_items_data:
            order_items.append(OrderItem(
                order=order,
                **item_data
            ))
            
            # Reserve inventory (decrease available, increase reserved)
            inv = inventories[item_data['product_id']]
            inv.reserved += item_data['quantity']
            inv.save(update_fields=['reserved'])
        
        OrderItem.objects.bulk_create(order_items)
        
        # Step 5: Clear the cart
        CartService().clear_cart(user_id)
        
        # Step 6: Queue payment + notification
        # These happen OUTSIDE the transaction (async)
        return order
    
    def confirm_payment(self, order_id: int, payment_ref: str):
        """Called by payment webhook after successful payment."""
        with transaction.atomic():
            order = Order.objects.select_for_update().get(id=order_id, status='pending')
            order.status = 'paid'
            order.payment_ref = payment_ref
            order.paid_at = timezone.now()
            order.save()
            
            # Deduct from actual quantity (reserved → sold)
            for item in order.items.all():
                Inventory.objects.filter(product_id=item.product_id).update(
                    quantity=F('quantity') - item.quantity,
                    reserved=F('reserved') - item.quantity
                )
        
        # Queue notifications (outside transaction)
        send_order_confirmation.delay(order_id)
    
    def cancel_order(self, order_id: int, user_id: int):
        """Cancel and release inventory reservation."""
        with transaction.atomic():
            order = Order.objects.select_for_update().get(
                id=order_id, user_id=user_id, status='pending'
            )
            order.status = 'cancelled'
            order.save()
            
            # Release reservations
            for item in order.items.all():
                Inventory.objects.filter(product_id=item.product_id).update(
                    reserved=F('reserved') - item.quantity
                )
```

---

## ⚡ Flash Sale System

### The Challenge

Flash sale starts → 100,000 users rush to buy → 100 units available
- Normal inventory system would be overwhelmed
- Need atomic counter operations

### Redis-Based Flash Sale Counter

```python
# apps/flash_sales/service.py
import redis
from redis.exceptions import WatchError

r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

def initialize_flash_sale(flash_sale_id: int, stock: int):
    """Called when flash sale starts (via Celery Beat)."""
    key = f"flash_sale:{flash_sale_id}:stock"
    r.set(key, stock, ex=3600)  # Expire after 1 hour max
    print(f"Flash sale {flash_sale_id} initialized with {stock} units")

def reserve_flash_sale_item(flash_sale_id: int, user_id: int) -> bool:
    """
    Atomically reserve one unit from flash sale stock.
    Uses Redis Lua script for atomic check-and-decrement.
    Returns True if reserved, False if out of stock.
    """
    # Lua script: atomic check and decrement
    lua_script = """
    local key = KEYS[1]
    local user_key = KEYS[2]
    
    -- Check if user already purchased
    if redis.call('EXISTS', user_key) == 1 then
        return -1  -- Already purchased
    end
    
    -- Check stock
    local stock = tonumber(redis.call('GET', key))
    if stock == nil or stock <= 0 then
        return 0  -- Out of stock
    end
    
    -- Decrement stock and mark user
    redis.call('DECR', key)
    redis.call('SET', user_key, '1', 'EX', 86400)  -- Remember for 24h
    
    return 1  -- Success
    """
    
    stock_key = f"flash_sale:{flash_sale_id}:stock"
    user_key = f"flash_sale:{flash_sale_id}:user:{user_id}"
    
    result = r.eval(lua_script, 2, stock_key, user_key)
    
    if result == 1:
        return True  # Reserved successfully
    elif result == -1:
        raise ValueError("You have already purchased this flash sale item")
    else:
        raise ValueError("Flash sale item is out of stock")

def get_flash_sale_stock(flash_sale_id: int) -> int:
    """Get remaining stock count."""
    key = f"flash_sale:{flash_sale_id}:stock"
    value = r.get(key)
    return int(value) if value else 0
```

### Flash Sale Order Flow

```python
# apps/orders/views.py

class FlashSaleOrderView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, flash_sale_id):
        try:
            flash_sale = FlashSale.objects.get(
                id=flash_sale_id,
                is_active=True,
                starts_at__lte=timezone.now(),
                ends_at__gte=timezone.now()
            )
        except FlashSale.DoesNotExist:
            return Response({'error': 'Flash sale not active'}, status=400)
        
        # Step 1: Try to reserve via Redis (fast, atomic, no DB hit)
        try:
            reserve_flash_sale_item(flash_sale_id, request.user.id)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        
        # Step 2: Create order at flash sale price
        try:
            order = OrderService().place_flash_sale_order(
                user_id=request.user.id,
                flash_sale=flash_sale,
                address_id=request.data.get('address_id')
            )
            return Response({'order_id': order.id}, status=201)
        except Exception as e:
            # If order creation fails, release the Redis reservation
            release_flash_sale_reservation(flash_sale_id, request.user.id)
            return Response({'error': str(e)}, status=500)
```

---

## 📦 Product Search (Elasticsearch)

```python
# apps/search/documents.py
from elasticsearch_dsl import Document, Text, Keyword, Float, Integer, Boolean

class ProductDocument(Document):
    name = Text(analyzer='english', fields={'raw': Keyword()})
    description = Text(analyzer='english')
    category_id = Integer()
    category_name = Keyword()
    seller_id = Integer()
    price = Float()
    rating = Float()
    total_sold = Integer()
    is_active = Boolean()
    
    class Index:
        name = 'products'

# Sync via Celery after product save
@shared_task
def sync_product_to_es(product_id):
    product = Product.objects.select_related('category', 'seller').get(id=product_id)
    doc = ProductDocument(
        meta={'id': product_id},
        name=product.name,
        description=product.description,
        category_id=product.category_id,
        category_name=product.category.name,
        price=float(product.price),
        is_active=product.is_active,
    )
    doc.save()

# Search
def search_products(query, category_id=None, min_price=None, max_price=None,
                    sort='relevance', page=1):
    s = ProductDocument.search()
    s = s.filter('term', is_active=True)
    
    if query:
        s = s.query('multi_match', query=query,
                    fields=['name^3', 'description'],
                    fuzziness='AUTO')
    
    if category_id:
        s = s.filter('term', category_id=category_id)
    
    if min_price or max_price:
        price_range = {}
        if min_price:
            price_range['gte'] = min_price
        if max_price:
            price_range['lte'] = max_price
        s = s.filter('range', price=price_range)
    
    sort_map = {
        'relevance': '_score',
        'price_asc': 'price',
        'price_desc': '-price',
        'popular': '-total_sold',
    }
    s = s.sort(sort_map.get(sort, '_score'))
    
    s = s[(page-1)*20: page*20]
    return s.execute()
```

---

## 📨 Notification Pipeline

```python
# apps/notifications/tasks.py

@shared_task(queue='email', max_retries=3)
def send_order_confirmation(order_id: int):
    order = Order.objects.select_related('user').prefetch_related('items__product').get(id=order_id)
    
    # Render HTML email template
    html_content = render_to_string('emails/order_confirmation.html', {'order': order})
    
    send_mail(
        subject=f'Order #{order.id} Confirmed! 🎉',
        message=f'Your order of {order.total_amount} BDT has been confirmed.',
        from_email='orders@marketflow.com',
        recipient_list=[order.user.email],
        html_message=html_content
    )

@shared_task(queue='sms')
def send_order_sms(order_id: int):
    order = Order.objects.select_related('user').get(id=order_id)
    
    # Send via SMS gateway (e.g., SSL Wireless for Bangladesh)
    send_sms(
        to=order.user.phone,
        message=f"MarketFlow: Order #{order.id} confirmed. Total: {order.total_amount} BDT. Track: marketflow.com/orders/{order.id}"
    )

# Celery Beat Schedules
app.conf.beat_schedule = {
    'sync-elasticsearch': {
        'task': 'apps.search.tasks.sync_products_to_es',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
    },
    'cleanup-expired-carts': {
        'task': 'apps.cart.tasks.cleanup_expired_carts',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2am
    },
    'send-abandoned-cart-emails': {
        'task': 'apps.cart.tasks.send_abandoned_cart_emails',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
}
```

---

## 📈 Scaling for Flash Sales (10x Traffic)

### Auto-scaling Strategy

```
Normal: 3 Django API servers
Flash sale announcement → pre-scale to 10 Django servers

How to pre-scale:
1. Admin sets flash sale 24h in advance
2. Celery Beat task triggers 30 minutes before sale
3. Task calls AWS Auto Scaling API to set min capacity = 10
4. After sale ends (via another scheduled task): scale back to 3
```

### Flash Sale Architecture (Simplified)

```
1,000,000 users hit "Buy Now" simultaneously

Layer 1: Nginx rate limiter
  - Max 5,000 requests/second to flash sale endpoint
  - Queue or reject excess with retry

Layer 2: Redis atomic counter
  - 100,000 requests hit Redis
  - Each atomic DECR: 1 microsecond
  - Only 100 succeed, rest get "out of stock" instantly
  - Redis handles this at millions of ops/second

Layer 3: DB order creation
  - Only 100 orders created (those who won the Redis lottery)
  - Normal DB load, no stampede
```

### Nginx Rate Limiting for Flash Sales

```nginx
# Separate rate limiting zone for flash sales
limit_req_zone $binary_remote_addr zone=flash_sale:10m rate=2r/s;

location /api/flash-sales/ {
    limit_req zone=flash_sale burst=5 nodelay;
    limit_req_status 429;
    proxy_pass http://api_servers;
}
```

---

## ❌ Failure Handling

### Payment Failure → Inventory Release

```python
# Payment webhook from Stripe
@api_view(['POST'])
def stripe_webhook(request):
    event = stripe.Webhook.construct_event(
        request.body, request.headers['Stripe-Signature'],
        settings.STRIPE_WEBHOOK_SECRET
    )
    
    if event['type'] == 'payment_intent.succeeded':
        order_id = event['data']['object']['metadata']['order_id']
        OrderService().confirm_payment(order_id, event['data']['object']['id'])
    
    elif event['type'] == 'payment_intent.payment_failed':
        order_id = event['data']['object']['metadata']['order_id']
        # Release inventory reservation
        OrderService().cancel_order_on_payment_failure(order_id)
    
    return Response({'status': 'handled'})
```

### Inventory Reconciliation Job

```python
@shared_task
def reconcile_inventory():
    """
    Daily job: check for stuck 'pending' orders and release their reservations.
    Handles cases where webhooks failed.
    """
    cutoff = timezone.now() - timedelta(hours=2)
    stuck_orders = Order.objects.filter(
        status='pending',
        created_at__lt=cutoff
    )
    
    for order in stuck_orders:
        logger.warning(f"Cancelling stuck order {order.id}")
        OrderService().cancel_order_admin(order.id)
```

---

## ⚖️ Trade-offs

| Decision | Trade-off |
|----------|----------|
| Redis for cart | Fast, but data loss on Redis failure (cart cleared) vs. DB (durable but slower) |
| SELECT FOR UPDATE | Prevents overselling but adds lock contention (vs. optimistic locking with retry) |
| Redis Lua for flash sale | Atomic, fast, but adds Redis as critical dependency |
| Snapshot product in order | Order history is accurate even if product is later deleted/modified (vs. JOIN to products with stale data risk) |
| Partition orders by date | Excellent query performance but adds operational complexity |
| Elasticsearch sync via Celery | Search index may be slightly stale (seconds) vs. synchronous update (slower writes) |
