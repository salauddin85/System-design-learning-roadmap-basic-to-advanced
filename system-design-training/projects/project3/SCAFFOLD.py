# MarketFlow — Project 3 Starter Scaffold
# The most complex project. Builds on everything learned.
# Use alongside PROJECT_3_SOLUTION.md.

# ─────────────────────────────────────────────
# FOLDER STRUCTURE
# ─────────────────────────────────────────────
#
# marketflow/
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
# │   ├── users/           (auth, addresses, profiles)
# │   ├── catalog/         (products, categories, inventory)
# │   ├── cart/            (Redis-backed cart service)
# │   ├── orders/          (order lifecycle, saga pattern)
# │   ├── payments/        (Stripe integration, webhooks)
# │   ├── flash_sales/     (Redis atomic flash sale counters)
# │   ├── search/          (Elasticsearch product search)
# │   └── notifications/   (email, SMS via Celery)
# │
# └── nginx/
#     └── conf.d/default.conf

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
elasticsearch-dsl==8.13.0
stripe==9.12.0
boto3==1.34.0
Pillow==10.3.0
python-json-logger==2.0.7
drf-spectacular==0.27.2
flower==2.0.1
"""

# ─────────────────────────────────────────────
# apps/catalog/models.py
# ─────────────────────────────────────────────
CATALOG_MODELS = """
from django.db import models
from django.conf import settings
from decimal import Decimal


class Category(models.Model):
    name      = models.CharField(max_length=100)
    slug      = models.SlugField(unique=True)
    parent    = models.ForeignKey('self', null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='children')
    image_url = models.TextField(blank=True)

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Seller(models.Model):
    user      = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    shop_name = models.CharField(max_length=200)
    rating    = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sellers'


class Product(models.Model):
    seller        = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name='products')
    category      = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    name          = models.CharField(max_length=500)
    slug          = models.SlugField(max_length=500, unique=True)
    description   = models.TextField(blank=True)
    price         = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sku           = models.CharField(max_length=100, unique=True, blank=True)
    is_active     = models.BooleanField(default=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['-created_at']),
        ]

    @property
    def primary_image_url(self):
        img = self.images.filter(is_primary=True).first()
        return img.url if img else ''


class ProductImage(models.Model):
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    url        = models.TextField()
    thumbnail  = models.TextField(blank=True)
    is_primary = models.BooleanField(default=False)
    position   = models.SmallIntegerField(default=0)

    class Meta:
        db_table = 'product_images'
        ordering = ['position']


class Inventory(models.Model):
    product   = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inventory',
                                      primary_key=True)
    quantity  = models.IntegerField(default=0)
    reserved  = models.IntegerField(default=0)   # In carts / pending orders
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inventory'

    @property
    def available(self):
        return self.quantity - self.reserved


class FlashSale(models.Model):
    product         = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='flash_sales')
    flash_price     = models.DecimalField(max_digits=10, decimal_places=2)
    available_stock = models.IntegerField()
    starts_at       = models.DateTimeField()
    ends_at         = models.DateTimeField()
    is_active       = models.BooleanField(default=True)

    class Meta:
        db_table = 'flash_sales'
"""

# ─────────────────────────────────────────────
# apps/orders/models.py
# ─────────────────────────────────────────────
ORDER_MODELS = """
from django.db import models
from django.conf import settings


class Order(models.Model):
    STATUS_PENDING    = 'pending'
    STATUS_PAID       = 'paid'
    STATUS_PROCESSING = 'processing'
    STATUS_SHIPPED    = 'shipped'
    STATUS_DELIVERED  = 'delivered'
    STATUS_CANCELLED  = 'cancelled'
    STATUS_REFUNDED   = 'refunded'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAID, 'Paid'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_SHIPPED, 'Shipped'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_REFUNDED, 'Refunded'),
    ]

    user             = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                          related_name='orders')
    status           = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
    subtotal         = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_cost    = models.DecimalField(max_digits=10, decimal_places=2, default=60)
    discount         = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount     = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_address = models.JSONField()         # Snapshot at time of order
    payment_method   = models.CharField(max_length=50, blank=True)
    payment_ref      = models.CharField(max_length=200, blank=True)
    notes            = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    paid_at          = models.DateTimeField(null=True, blank=True)
    shipped_at       = models.DateTimeField(null=True, blank=True)
    delivered_at     = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'orders'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]


class OrderItem(models.Model):
    order            = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product          = models.ForeignKey('catalog.Product', on_delete=models.PROTECT)
    quantity         = models.IntegerField()
    unit_price       = models.DecimalField(max_digits=10, decimal_places=2)
    product_snapshot = models.JSONField()   # Snapshot: name, image, SKU at order time

    class Meta:
        db_table = 'order_items'
"""

# ─────────────────────────────────────────────
# apps/cart/service.py — Key business logic
# ─────────────────────────────────────────────
CART_SERVICE_HINT = """
# The CartService uses Redis Hash data structure.
# Key:   cart:user:{user_id}
# Field: product:{product_id}
# Value: JSON with {product_id, quantity, price, name, image, max_stock}
# TTL:   7 days (renewed on every cart operation)

# IMPLEMENT THESE METHODS:
# - get_cart(user_id) → dict
# - add_to_cart(user_id, product_id, quantity) → dict
# - update_quantity(user_id, product_id, quantity) → dict
# - remove_from_cart(user_id, product_id)
# - clear_cart(user_id)
# - get_cart_count(user_id) → int

# See PROJECT_3_SOLUTION.md for full implementation.
"""

# ─────────────────────────────────────────────
# apps/orders/services.py — Critical path
# ─────────────────────────────────────────────
ORDER_SERVICE_HINT = """
# The OrderService.place_order() method is the most critical piece.
# It must:
# 1. Start a database transaction
# 2. Lock inventory rows: Inventory.objects.select_for_update()
# 3. Validate stock for ALL items before proceeding
# 4. Create the Order record
# 5. Create OrderItem records
# 6. Update inventory.reserved += quantity for each item
# 7. Clear the cart
# 8. Commit the transaction
# 9. AFTER transaction: queue async tasks (email, SMS)

# CRITICAL: select_for_update() prevents race conditions.
# Without it, two simultaneous orders can oversell.

# See PROJECT_3_SOLUTION.md for complete implementation.
"""

# ─────────────────────────────────────────────
# config/celery.py — Task routing
# ─────────────────────────────────────────────
CELERY_CONFIG = """
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
app = Celery('marketflow')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.task_routes = {
    'apps.orders.tasks.*':        {'queue': 'critical'},
    'apps.payments.tasks.*':      {'queue': 'critical'},
    'apps.notifications.tasks.send_order_*': {'queue': 'email'},
    'apps.notifications.tasks.send_sms_*':   {'queue': 'sms'},
    'apps.search.tasks.*':        {'queue': 'default'},
}

app.conf.beat_schedule = {
    'sync-products-to-es': {
        'task': 'apps.search.tasks.sync_pending_products',
        'schedule': 600.0,  # Every 10 minutes
    },
    'reconcile-inventory': {
        'task': 'apps.orders.tasks.reconcile_inventory',
        'schedule': 3600.0,  # Every hour
    },
    'activate-flash-sales': {
        'task': 'apps.flash_sales.tasks.activate_due_flash_sales',
        'schedule': 30.0,  # Every 30 seconds
    },
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
      POSTGRES_DB: marketflow
      POSTGRES_USER: marketflow
      POSTGRES_PASSWORD: marketflow_pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"

  elasticsearch:
    image: elasticsearch:8.13.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data

  api:
    build: .
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 60
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://marketflow:marketflow_pass@db:5432/marketflow
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - DEBUG=True
    depends_on:
      - db
      - redis
      - elasticsearch

  worker-critical:
    build: .
    command: celery -A config worker -l info -Q critical --concurrency=8
    environment:
      - DATABASE_URL=postgresql://marketflow:marketflow_pass@db:5432/marketflow
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis

  worker-default:
    build: .
    command: celery -A config worker -l info -Q default,email,sms --concurrency=4
    environment:
      - DATABASE_URL=postgresql://marketflow:marketflow_pass@db:5432/marketflow
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis

  beat:
    build: .
    command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    depends_on:
      - worker-critical

  flower:
    build: .
    command: celery -A config flower --port=5555
    ports:
      - "5555:5555"
    depends_on:
      - worker-critical

volumes:
  postgres_data:
  es_data:
"""

print("MarketFlow Scaffold ready.")
print("This is the most complex project — start with catalog → cart → orders → payments")
print("Refer to PROJECT_3_SOLUTION.md for the inventory locking and flash sale implementation.")
