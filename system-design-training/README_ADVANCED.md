# 📕 System Design Training — ADVANCED LEVEL
### Designing Large-Scale Distributed Systems

---

## 🧭 Introduction

Welcome to the Advanced level — where you think at the scale of millions of users, design for failure, and architect systems that stay running even when parts of them break.

This is the level that separates mid-level engineers from senior engineers. You'll learn to design systems like Uber, Netflix, and WhatsApp, and understand the deep trade-offs that make these systems work at massive scale.

---

## ✅ Prerequisites

You must be comfortable with:
- All Intermediate level concepts
- Redis, Celery, load balancing, API design
- Docker and basic deployment concepts
- SQL and NoSQL databases

---

## 🗺️ Learning Roadmap

---

## STEP 1: CAP Theorem

### 📖 Concept Explanation

**CAP Theorem** (by Eric Brewer, 2000) states that a distributed system can only guarantee 2 out of 3 of the following properties at the same time:

- **C — Consistency:** Every read receives the most recent write (all nodes return the same data)
- **A — Availability:** Every request gets a response (no timeouts or errors), even if it's not the latest data
- **P — Partition Tolerance:** The system continues to work even when the network between nodes is broken (network partition)

**The brutal reality:** In a distributed system, network partitions WILL happen. So you must choose: **CP or AP**?

### 📊 Visualization

```
           Consistency
               /\
              /  \
             /    \
            /  ??? \
           /        \
          /----------\
Availability      Partition
                  Tolerance

You can only be in one corner or on one edge.
In real distributed systems, P is required.
So the real choice is: C vs A
```

**CP Systems (choose Consistency over Availability):**
- During a network partition, the system refuses to respond (returns error) rather than return stale data
- Examples: PostgreSQL, ZooKeeper, HBase, Redis (in cluster mode)
- Use when: Banking, inventory management (you CANNOT show wrong stock)

**AP Systems (choose Availability over Consistency):**
- During a network partition, the system still responds but may return stale data
- Eventually consistent — data will sync once the partition heals
- Examples: Cassandra, DynamoDB, CouchDB, DNS
- Use when: Social media likes/counts, shopping cart, product recommendations

### 🌍 Real-World Examples

**Bank transfer (CP required):**
```
You have $100. You transfer $80 to two ATMs at once.
If consistency fails → you withdraw $160 (bank loses $60)
CAP choice: Consistency MUST be prioritized. Block the request if nodes disagree.
```

**Amazon shopping cart (AP preferred):**
```
You add an item to cart.
Network hiccup means one server doesn't see the update.
AP: Return the cart (possibly without the item) rather than error.
The item will sync eventually.
Amazon chose: "Empty cart errors are worse than showing slightly stale cart"
```

### 📊 PACELC — Extension of CAP

PACELC extends CAP by also considering **latency trade-offs even without partitions**:

```
If Partition:     choose between A and C
Else (no partition): choose between L (Latency) and C (Consistency)

Systems tuned for low latency may return stale data.
Systems tuned for consistency introduce latency for coordination.
```

### ✅ Best Practices

- Know your system's consistency requirements before choosing a database
- Design different parts of your system with different CAP trade-offs
- "Eventual consistency" is often fine for most data (not financial transactions)

### ❌ Common Mistakes

- Treating CAP as a database property rather than a design choice
- Choosing CP for everything (kills availability unnecessarily)
- Not understanding that "consistency" in CAP is linearizability (very strict)

### 📝 Assignment 1

**Task:** For each of the following features, choose CP or AP and justify:
1. User balance in a digital wallet app
2. "Number of likes" on a social media post
3. Product inventory count on e-commerce site
4. User login session
5. Real-time chat messages
6. Stock price display
7. Recommendation algorithm results

For each: Which would you choose and what are the trade-offs?

---

## STEP 2: Distributed Systems Fundamentals

### 📖 Concept Explanation

A **distributed system** is a collection of independent computers that appear to users as a single coherent system.

**Key challenges in distributed systems:**

### 📊 1. Fallacies of Distributed Computing

These are common wrong assumptions developers make:

```
1. The network is reliable         → Networks fail all the time
2. Latency is zero                 → Every network hop adds latency
3. Bandwidth is infinite           → You can't send unlimited data
4. The network is secure           → Assume adversaries exist
5. Topology doesn't change         → Servers restart, IPs change
6. There is one administrator      → Multiple teams, conflicts
7. Transport cost is zero          → Serialization, transmission costs
8. The network is homogeneous      → Different hardware, OS, versions
```

### 📊 2. Consistency Models

In distributed systems, different consistency guarantees exist:

```
STRONG CONSISTENCY (linearizability):
All reads see the most recent write, immediately.
[Write A] → [Read] → Must return A
Used by: RDBMS with synchronous replication, ZooKeeper

SEQUENTIAL CONSISTENCY:
Operations happen in some order, but all nodes agree on that order.
Less strict than linearizability.

CAUSAL CONSISTENCY:
If A causes B, everyone sees A before B.
Unrelated events can be in any order.

EVENTUAL CONSISTENCY:
Given no new updates, all replicas will converge to the same value.
Most available NoSQL databases.

[Write A] → [Read] → May return old value temporarily
           → [Read 10s later] → Returns A (eventually consistent)
```

### 📊 3. Distributed Consensus — Raft Algorithm

How do distributed nodes agree on a single value? This is the consensus problem.

**Raft** is a consensus algorithm:
```
Raft has 3 roles:
- Leader: Accepts all writes, replicates to followers
- Follower: Accepts data from leader, votes in elections
- Candidate: Running for leader election

Election:
1. No heartbeat from leader → Follower becomes Candidate
2. Candidate asks for votes
3. Majority votes → New leader elected
4. New leader starts accepting writes

Log Replication:
1. Client sends write to Leader
2. Leader writes to its log
3. Leader sends log entry to all Followers
4. Majority acknowledge → Leader commits
5. Leader responds to client
```

### 📊 4. Clock Skew and Distributed Time

In distributed systems, different servers have different clocks. You can't rely on timestamps for ordering!

**Solutions:**
- **Logical clocks (Lamport clocks):** Not real time, but ordering
- **Vector clocks:** Track causality across nodes
- **Google TrueTime:** Atomic clocks in datacenters + GPS (used in Spanner)

### 📊 5. Idempotency — Critical for Distributed Systems

An operation is **idempotent** if calling it multiple times has the same effect as calling it once.

```
Why it matters:
- Network failures cause retries
- If not idempotent, retries cause duplicate operations
- "Pay $100" retried 3 times → charge $300! ❌

Solution: Idempotency Keys
Client sends: POST /payments
Headers: Idempotency-Key: unique-uuid-per-request

Server:
1. Check if idempotency key exists in Redis
2. If yes → return previous result (no duplicate processing)
3. If no → process, store result with key, return result
```

```python
# Django idempotency middleware
def process_payment(request):
    idempotency_key = request.headers.get('Idempotency-Key')
    if not idempotency_key:
        return Response({'error': 'Idempotency-Key header required'}, status=400)
    
    # Check if already processed
    cache_key = f"idempotency:{idempotency_key}"
    cached_result = redis.get(cache_key)
    if cached_result:
        return Response(json.loads(cached_result))  # Return same result
    
    # Process payment
    result = charge_payment(request.data)
    
    # Store result (24 hour TTL)
    redis.setex(cache_key, 86400, json.dumps(result))
    
    return Response(result)
```

### 📝 Assignment 2

**Task:** Design the architecture for a distributed counter system (like YouTube view counts):

1. The counter must handle 1 million increments per second
2. Exact consistency is not required (approximate is fine)
3. The displayed count can be slightly behind real count
4. Design the system — how would you aggregate counts?
5. What consistency model is appropriate? Why?
6. How would you ensure the system works even if one node fails?

---

## STEP 3: Event-Driven Architecture

### 📖 Concept Explanation

**Event-Driven Architecture (EDA)** is a design pattern where services communicate by producing and consuming events (things that happened) rather than calling each other directly.

**Event:** Something that happened in the past. "Order was placed." "Payment was processed." "User registered."

**Three models:**

1. **Event Notification:** "Something happened" — receiver decides what to do
2. **Event-Carried State Transfer:** Event contains all the data needed (no callbacks)
3. **Event Sourcing:** Events are the source of truth — system state is derived from event history

### 📊 EDA vs Request/Response

```
REQUEST/RESPONSE (synchronous):
[Order Service] ---> "Create payment" ---> [Payment Service]
[Order Service] <--- "Payment result" <--- [Payment Service]
Order service WAITS for payment to complete.
Tight coupling: if Payment Service is down, Order Service fails.

EVENT-DRIVEN (asynchronous):
[Order Service] ---> Event: "OrderPlaced" ---> [Event Bus]
                                               [Payment Service] subscribes → processes payment
                                               [Email Service] subscribes → sends confirmation
                                               [Analytics Service] subscribes → records event
Order service doesn't wait. It doesn't even know who's listening.
Loose coupling: Payment Service down? Events queue up and process when it recovers.
```

### 📊 Event Sourcing

Instead of storing current state, store the sequence of events that led to that state.

```
Traditional (Store Current State):
[users table: id=1, name=Rahim, balance=500]
When balance changes → UPDATE balance = 500

Event Sourcing (Store Events):
Event 1: UserCreated {name: Rahim, balance: 0}
Event 2: MoneyDeposited {amount: 1000}
Event 3: MoneyWithdrawn {amount: 500}
Current state: balance = 0 + 1000 - 500 = 500 ✅

Benefits:
- Complete audit trail (who did what, when)
- Can replay events to rebuild state
- Can create "projections" - different views of the same data
- Time travel: what was the state on Jan 1st? Replay events up to that point

Used by: Financial systems, git (version control is event sourcing!), Kafka
```

### 📊 CQRS — Command Query Responsibility Segregation

Often used with Event Sourcing:

```
CQRS Pattern:
- WRITE side (Commands): "Place order", "Update profile" → Write to Event Store
- READ side (Queries): "Get order history", "Show dashboard" → Read from optimized Read Models

                [Client]
               /         \
          [Write API]   [Read API]
              |               |
        [Event Store]   [Read Models]
              |         (optimized for queries)
              |→ events → [Projection Builder] → Updates Read Models
```

**Why?**
- Write operations have different scaling needs than reads
- Read models can be optimized for specific query patterns (denormalized)
- You can have multiple read models for different use cases

### 🌍 Real-World Example: Uber's Ride Events

```
Events in a ride:
1. RideRequested {rider_id, pickup, dropoff, timestamp}
2. DriverAccepted {driver_id, ride_id, timestamp}
3. DriverArrived {ride_id, location, timestamp}
4. RideStarted {ride_id, timestamp}
5. RideCompleted {ride_id, distance, duration, timestamp}
6. PaymentProcessed {ride_id, amount, method, timestamp}
7. RatingSubmitted {ride_id, rating, timestamp}

These events flow through Kafka to:
- Billing service (subscribes to RideCompleted, PaymentProcessed)
- Analytics service (subscribes to everything)
- Driver earnings service (subscribes to RideCompleted)
- Notification service (subscribes to DriverAccepted, RideStarted, etc.)
```

### ✅ Best Practices

- Events should be immutable (never change a past event)
- Include event version and schema for evolution
- Design events to be self-contained (no lookups needed)
- Use event IDs for idempotency
- Handle out-of-order events (they happen in distributed systems)

### ❌ Common Mistakes

- Making events too fine-grained (too many tiny events)
- Not versioning event schemas
- Not handling eventual consistency in the UI
- Using EDA for simple, synchronous workflows

### 📝 Assignment 3

**Task:** Design an event-driven e-commerce system:

1. List all events that can happen from "User clicks Buy" to "Product delivered"
2. For each event, identify which services publish it and which subscribe
3. Draw the event flow diagram
4. A payment event is processed twice (duplicate) — how does idempotency help?
5. The warehouse service is down for 2 hours — what happens to events? How does the system recover?

---

## STEP 4: Microservices Architecture (Deep Dive)

### 📖 Concept Explanation

We introduced microservices in basics. Now let's go deep into how they work in practice.

### 📊 Microservices Communication

**Synchronous (HTTP/gRPC):**
```
[Service A] ---HTTP GET---> [Service B] ---HTTP GET---> [Service C]
            <---response---             <---response---
```
Problem: If C is slow, A and B wait. Cascading failures.

**Asynchronous (Message Queue):**
```
[Service A] --> [Kafka topic] --> [Service B]
                              --> [Service C]
A doesn't wait. B and C process independently.
```

**gRPC (alternative to REST):**
- Uses Protocol Buffers (binary format, faster than JSON)
- Strongly typed interfaces
- Better for internal service-to-service communication
- Supports streaming

```protobuf
// user.proto
service UserService {
    rpc GetUser(GetUserRequest) returns (User);
    rpc StreamUserEvents(UserEventsRequest) returns (stream UserEvent);
}

message GetUserRequest {
    int32 user_id = 1;
}

message User {
    int32 id = 1;
    string name = 2;
    string email = 3;
}
```

### 📊 Service Discovery

In microservices, services need to find each other. How?

```
Option 1: Client-side discovery
[Service A] → asks [Service Registry: Consul/Eureka] → "Where is Service B?"
Service Registry responds: "192.168.1.10:8001"
Service A calls Service B directly.

Option 2: Server-side discovery (preferred with Kubernetes)
[Service A] → calls [Load Balancer / K8s Service]
Load Balancer knows all healthy instances of Service B
Routes to one automatically
```

**In Kubernetes:**
```yaml
# Service B registers as a Kubernetes Service
apiVersion: v1
kind: Service
metadata:
  name: payment-service
spec:
  selector:
    app: payment
  ports:
    - port: 80
      targetPort: 8000
```

Service A just calls `http://payment-service/payments` — Kubernetes handles routing!

### 📊 Saga Pattern — Distributed Transactions

In microservices, you can't use traditional database transactions across services. **Saga** is the solution.

**Example: E-commerce order placement**

```
Order requires:
1. Reserve inventory (Inventory Service)
2. Process payment (Payment Service)
3. Create shipment (Shipping Service)

If step 3 fails, we need to:
- Cancel shipment (compensating action)
- Refund payment (compensating action)
- Release inventory (compensating action)

This chain of actions + compensating actions = Saga
```

**Choreography-based Saga (event-driven):**
```
[Order Service] → publishes: OrderPlaced
[Inventory Service] subscribes → reserves stock → publishes: StockReserved
[Payment Service] subscribes → charges card → publishes: PaymentProcessed
[Shipping Service] subscribes → creates shipment → publishes: ShipmentCreated

If Payment fails:
[Payment Service] → publishes: PaymentFailed
[Inventory Service] subscribes → releases reserved stock
[Order Service] subscribes → cancels order
```

**Orchestration-based Saga (centralized):**
```
[Saga Orchestrator] → calls Inventory Service → reserves stock
                    → calls Payment Service → processes payment
                    → calls Shipping Service → creates shipment
If any fails: Orchestrator calls compensating actions in reverse
```

### 📊 Strangler Fig Pattern — Migrating from Monolith

```
How to migrate without rewriting everything:

Phase 1: Start with monolith
[All requests] → [Monolith]

Phase 2: Extract first microservice (e.g., Auth)
[All requests] → [API Gateway]
                      |
                      |→ /auth/* → [Auth Microservice] ← NEW
                      |→ /api/*  → [Monolith]

Phase 3: Extract more services
[All requests] → [API Gateway]
                      |
                      |→ /auth/*    → [Auth Service]
                      |→ /products/* → [Product Service]
                      |→ /api/*     → [Monolith] ← Shrinking

Phase 4: Monolith is strangled (replaced piece by piece)
```

### ✅ Best Practices

- Each service should own its data (no shared databases)
- Design for failure (service B might be down when A calls it)
- Use asynchronous communication where possible
- Version your service APIs
- Each service should be independently deployable

### ❌ Common Mistakes

- Shared databases across microservices
- Synchronous chains that are too long (A→B→C→D→E = 5x latency, 5x failure points)
- Not implementing circuit breakers
- Distributed monolith (everything calls everything synchronously)

### 📝 Assignment 4

**Task:** Design the microservices architecture for a bank:

1. Identify at least 5 microservices (name them and their responsibility)
2. Draw the service communication diagram (use arrows to show dependencies)
3. The user wants to transfer money between accounts. Design the Saga for this transaction.
4. If the notification service is down, should the transfer fail? Why or why not?
5. How would you handle the database for each service?

---

## STEP 5: Message Queues — Kafka Deep Dive

### 📖 Concept Explanation

**Apache Kafka** is a distributed streaming platform designed for high-throughput, fault-tolerant messaging.

Kafka is not just a queue — it's an **immutable, distributed commit log**.

### 📊 Kafka Concepts

```
TOPIC: A named category/channel for messages (like "orders", "payments", "clicks")

PARTITION: Topics are split into partitions for parallel processing
  Topic "orders": [Partition 0] [Partition 1] [Partition 2]
  Each partition is an ordered, immutable log of messages

PRODUCER: Sends messages to topics
CONSUMER: Reads messages from topics
CONSUMER GROUP: Multiple consumers share reading of a topic

BROKER: A Kafka server (usually 3+ in production)
CLUSTER: Multiple brokers together
ZOOKEEPER/KRaft: Manages the cluster metadata

OFFSET: Position of a message within a partition
  Partition 0: [msg0, msg1, msg2, msg3, msg4...]
                  ↑                        ↑
               offset=0               current offset (consumer reads here)
```

### 📊 Kafka Architecture

```
Producers                 Kafka Cluster                   Consumers
                     +---------------------------+
[Order Service]  →   |  Broker 1                 |   → [Consumer Group A]
[User Service]   →   |  Topic: orders             |   → (Analytics Service)
[Payment Service]→   |    Partition 0 ─────────── |→    Consumer 1: reads P0
                     |    Partition 1 ─────────── |→    Consumer 2: reads P1
                     |    Partition 2 ─────────── |→    Consumer 3: reads P2
                     |                            |
                     |  Broker 2 (replica)        |   → [Consumer Group B]
                     |  Topic: orders (replica)   |   → (Billing Service)
                     +---------------------------+      Different offset, same msgs
```

### 📊 Kafka vs RabbitMQ

| Feature | Kafka | RabbitMQ |
|---------|-------|---------|
| Model | Log-based (messages persist) | Queue-based (messages deleted after ack) |
| Throughput | Millions/sec | Thousands/sec |
| Message retention | Days/weeks (configurable) | Until consumed |
| Replay | Yes (seek to offset) | No |
| Best for | Event streaming, analytics, event sourcing | Task queues, RPC |
| Ordering | Per partition | Per queue |
| Use case | Log aggregation, stream processing | Email sending, job queue |

### 📊 Kafka in Python

```python
from confluent_kafka import Producer, Consumer

# Producer
producer = Producer({'bootstrap.servers': 'localhost:9092'})

def publish_event(topic, key, value):
    producer.produce(
        topic=topic,
        key=str(key).encode('utf-8'),
        value=json.dumps(value).encode('utf-8'),
        callback=delivery_callback
    )
    producer.flush()  # Ensure delivery

# Publish an order event
publish_event('orders', order_id, {
    'event': 'OrderPlaced',
    'order_id': order_id,
    'user_id': user_id,
    'items': items,
    'timestamp': datetime.utcnow().isoformat()
})

# Consumer
consumer = Consumer({
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'billing-service',
    'auto.offset.reset': 'earliest'  # Start from beginning if new group
})
consumer.subscribe(['orders'])

while True:
    msg = consumer.poll(timeout=1.0)
    if msg is None:
        continue
    if msg.error():
        handle_error(msg.error())
        continue
    
    event = json.loads(msg.value())
    
    if event['event'] == 'OrderPlaced':
        process_billing(event)
    
    consumer.commit()  # Acknowledge message processed
```

### 📊 Kafka Partitioning Strategy

```python
# Messages with same key go to same partition (ordering guaranteed)
producer.produce(
    topic='orders',
    key=str(user_id).encode(),  # All orders from same user → same partition
    value=json.dumps(order_event).encode()
)

# This ensures:
# - Order events for one user are processed in order
# - Different users' events can be processed in parallel
```

### 🌍 Real-World Use Cases

| Company | How They Use Kafka |
|---------|-------------------|
| LinkedIn | Activity feeds, metrics (1.4 trillion messages/day) |
| Uber | Real-time analytics, event streaming |
| Netflix | Real-time monitoring, recommendation engine |
| Airbnb | Change data capture, analytics |

### 📝 Assignment 5

**Task:** Design a real-time analytics system for an e-commerce platform using Kafka:

1. Define 5 event types (topics) and their schema
2. Design the producer (which services publish what)
3. Design 3 different consumer groups and what they do with the events
4. A consumer is down for 2 hours — what happens? How does it recover?
5. How many partitions would you use for the "page_views" topic that gets 100,000 events/second? Why?

---

## STEP 6: System Design Patterns

### 📖 Concept Explanation

**Pattern 1: Circuit Breaker**

Named after electrical circuit breakers. Prevents cascading failures.

```
States:
CLOSED → Normal operation. Requests flow through.
OPEN   → Service is failing. Block all requests immediately (fast fail).
HALF-OPEN → Probe: let a few requests through to check if service recovered.

Flow:
[Closed] → 5 failures in 60s → [Open] → 30s timeout → [Half-Open]
[Half-Open] → success → [Closed]
[Half-Open] → failure → [Open]
```

```python
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit is OPEN - service unavailable")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

**Pattern 2: Bulkhead**

Isolate failures — just like a ship's bulkhead partitions prevent one flooded compartment from sinking the whole ship.

```
Without Bulkhead:
[All requests share one thread pool]
Slow requests → exhaust threads → ALL requests fail

With Bulkhead:
[API requests → Thread Pool 1: 50 threads]
[DB queries → Thread Pool 2: 20 threads]  
[External API → Thread Pool 3: 10 threads]
External API slow → only its 10 threads affected, rest unaffected
```

**Pattern 3: Retry with Exponential Backoff**

```python
import time
import random

def call_with_retry(func, max_retries=3, base_delay=1, max_delay=60):
    for attempt in range(max_retries):
        try:
            return func()
        except TransientError as e:
            if attempt == max_retries - 1:
                raise  # Final attempt failed
            
            # Exponential backoff with jitter
            delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
            print(f"Attempt {attempt + 1} failed. Retrying in {delay:.2f}s...")
            time.sleep(delay)
```

**Pattern 4: Strangler Fig** (covered in microservices)

**Pattern 5: API Gateway Pattern** (covered in intermediate)

**Pattern 6: Sidecar Pattern**

```
In Kubernetes/Docker, attach a "sidecar" container to your main app container.
The sidecar handles cross-cutting concerns:
- Logging (collect logs, forward to Elasticsearch)
- Service mesh (Envoy proxy for traffic management)
- Secret injection
- Health checking

[Pod]
  ├── [Main App Container]
  └── [Sidecar Container] ← handles logging, mTLS, tracing
```

**Pattern 7: Database per Service**

```
Each microservice has its OWN database.
They cannot directly query each other's databases.
Communication only through APIs or events.

[Order Service] → [Order DB: PostgreSQL]
[Product Service] → [Product DB: PostgreSQL]
[Cart Service] → [Cart DB: Redis]
[Search Service] → [Search DB: Elasticsearch]
```

### 📝 Assignment 6

**Task:**

1. A payment service calls a fraud detection service. The fraud service is slow during peak hours.
   - Implement circuit breaker logic (pseudocode)
   - What should happen when the circuit is OPEN? (Allow payments? Block? Use fallback?)

2. Your Django API calls 3 external services (SMS, email, push notification).
   - Design a bulkhead pattern using Celery queues
   - What happens if the SMS service is down?

---

## STEP 7: High Availability & Fault Tolerance

### 📖 Concept Explanation

**High Availability (HA):** The system remains operational for as high a percentage of time as possible.

**Fault Tolerance:** The system continues to function correctly even when parts of it fail.

### 📊 HA Design Patterns

**Active-Passive (Master-Standby):**
```
[Load Balancer]
      |
      +--→ [Primary Server] ←── handles all traffic
      |
      +--→ [Standby Server] ←── warm standby, monitors primary
                                If primary fails → standby takes over (failover)
```

**Active-Active (Multi-master):**
```
[Load Balancer]
      |
      +--→ [Server 1] ←── handles 50% of traffic
      |
      +--→ [Server 2] ←── handles 50% of traffic
Both active simultaneously. If one fails → other handles 100%.
```

**Multi-Region Design:**
```
               [Global DNS with GeoDNS]
              /                        \
    [US-EAST Region]              [ASIA Region]
    [Load Balancer]               [Load Balancer]
    [App Servers x3]              [App Servers x3]
    [DB Primary]                  [DB Primary]
    [DB Replica]                  [DB Replica]
           \                            /
            \____[Cross-region replication]
```

### 📊 Chaos Engineering

Netflix's **Chaos Monkey** randomly terminates servers in production to find failure points before they cause outages.

```
Principles:
1. Define "normal" system behavior
2. Hypothesize about what happens when X fails
3. Inject chaos: kill servers, slow network, corrupt data
4. Observe what actually happens
5. Fix gaps between hypothesis and reality

Tools:
- Netflix Chaos Monkey
- AWS Fault Injection Simulator
- Gremlin
```

### 📊 Database High Availability

```
PostgreSQL HA with Patroni:
[Primary DB] ←→ [Patroni] ← manages
[Replica 1]  ←→ [Patroni]   failover
[Replica 2]  ←→ [Patroni]

[etcd cluster] ← holds lock for who is primary

If primary dies:
1. Patroni detects failure
2. Replicas hold an election (via etcd)
3. Most up-to-date replica becomes new primary
4. Other replicas reconfigure to follow new primary
5. Load balancer (HAProxy) updated automatically
All in ~30 seconds!
```

### 🌍 Case Study: Netflix Multi-Region

Netflix serves 220+ million subscribers globally.
- Uses AWS in 3 regions: US-EAST, US-WEST, EU-WEST
- Data is replicated across all regions
- If one region has an outage, traffic is automatically routed to healthy regions
- CDN (Open Connect) caches video in ISPs worldwide

### 📝 Assignment 7

**Task:** Design a high availability architecture for a banking API:

1. The bank needs 99.99% uptime (max 52 minutes downtime/year)
2. Design multi-region setup (Bangladesh + Singapore)
3. How does failover work if the Bangladesh region goes down?
4. How do you handle database replication lag between regions?
5. What monitoring/alerting would trigger a failover?
6. Design a runbook for "Database primary is unresponsive"

---

## STEP 8: Real-World System Design Case Studies

### 📖 Case Study 1: Design Uber

**Scale:** 5 million rides per day, drivers updating location every 4 seconds

**Key Requirements:**
- Match riders to nearest available drivers (< 5 seconds)
- Real-time tracking of driver location
- Surge pricing
- Payments

**Architecture:**

```
[Rider App] ←websocket→ [WebSocket Gateway]
[Driver App] ←websocket→ [WebSocket Gateway]
                |
        [Location Service]
                |
        [Geospatial Index]  ← stores driver locations
        (Redis GEOADD)       ← updated every 4 seconds
                |
        [Matching Service]
                |
        [Trip Service] → [Kafka: trip events]
                              ↓
                    [Payment Service] [Notification Service] [Analytics]
```

**Driver Location System:**
```python
# Redis Geo commands for location
redis.geoadd("drivers:active", longitude, latitude, driver_id)

# Find drivers within 2km of rider
nearby_drivers = redis.georadius(
    "drivers:active",
    rider_longitude, rider_latitude,
    2, unit="km",
    sort="ASC",  # Nearest first
    count=10     # Top 10 nearest
)
```

**Surge Pricing:**
```
Algorithm:
1. Count requests in an area in last 5 minutes
2. Count available drivers in same area
3. demand_ratio = requests / drivers
4. surge_multiplier = 1.0 + (demand_ratio - 1) * 0.5 (capped at 3.0x)
```

---

### 📖 Case Study 2: Design Netflix

**Scale:** 220M+ subscribers, 15% of global internet bandwidth

**Key Challenges:**
- Stream HD/4K video to millions simultaneously
- Fast startup time (< 1 second buffer)
- Personalized recommendations

**Architecture:**

```
[User] → [AWS API Gateway] → [Microservices]
                                  |
                [Recommendation Service] → Spark/ML
                [Search Service] → Elasticsearch
                [Billing Service] → PostgreSQL
                [Streaming Service] → Proprietary CDN (Open Connect)

Video Delivery:
[User in Dhaka]
     ↓
[Open Connect CDN node in ISP's network in Dhaka]
     ↓ (cache miss)
[Open Connect CDN in Singapore]
     ↓ (cache miss)
[Netflix Origin servers in AWS]

Most content is cached at ISP level → sub-second start time
```

**Netflix Open Connect:**
Netflix ships physical servers to ISPs. Content is pre-loaded onto these servers. Users never actually hit Netflix's AWS servers for video — they get it from these boxes.

---

### 📖 Case Study 3: Design WhatsApp

**Scale:** 2 billion users, 100 billion messages/day

**Key Requirements:**
- Deliver messages reliably (even if receiver is offline)
- Real-time delivery (push when online)
- End-to-end encryption
- Message status (sent, delivered, read)

**Architecture:**

```
[User A sends message]
     ↓
[WhatsApp Client SDK] → encrypts message client-side
     ↓
[WhatsApp Server]
     |
     ├→ Is User B online? → YES → Push via WebSocket connection
     |                   → NO  → Store in message queue
     |                           Deliver when B comes online
     |
     ├→ [Message Store Service] → store message (Mnesia/custom)
     ├→ [Push Notification] → FCM/APNS if app not open
     └→ [Status Update] → mark as "delivered"

When User B reads message → [Read Receipt] → back to User A → double blue tick
```

**Scale secret:** WhatsApp runs on Erlang (BEAM VM) — designed for millions of concurrent lightweight processes. Each connection is a separate process.

---

### 📖 Case Study 4: Design a URL Shortener (bit.ly)

**Scale:** 1 billion URLs, 10 billion redirects/month

**Core Design:**

```
Creating a short URL:
1. Take long URL
2. Generate unique 7-character code (Base62 encoded: a-z, A-Z, 0-9 = 62 chars)
   62^7 = 3.5 trillion possible URLs ← enough!
3. Store: {short_code: "abc123x", long_url: "https://...", user_id, created_at}

Redirecting:
GET /{short_code}
→ Check Redis cache for short_code
  → HIT: redirect immediately (microseconds)
  → MISS: lookup DB, cache result, redirect

Database:
CREATE TABLE urls (
    short_code VARCHAR(8) PRIMARY KEY,
    long_url TEXT NOT NULL,
    user_id INT,
    click_count INT DEFAULT 0,
    created_at TIMESTAMP,
    expires_at TIMESTAMP
);

Index on short_code (it's the PRIMARY KEY, already indexed)
```

**Generating unique codes:**
```python
import base62
import hashlib

def generate_short_code(long_url: str) -> str:
    # Option 1: MD5 hash + take first 7 chars
    hash_val = int(hashlib.md5(long_url.encode()).hexdigest(), 16)
    return base62.encode(hash_val)[:7]

    # Option 2: Auto-increment ID + Base62 encode
    # ID 1000000 → base62 → "4C92"
    # Shorter, unique, no collision
```

**Handling 10 billion redirects/month (~3,800/second):**
```
- Heavy read traffic → Cache aggressively in Redis (TTL 24h for popular URLs)
- Database replicas for read scaling
- CDN for geographic distribution
- Async click counting (don't update DB on every redirect — batch update every minute)
```

### 📝 Assignment 8 (Final Advanced Assignment)

**Task:** Design Twitter/X at scale (500M users, 500M tweets/day):

Your design must address:
1. **Tweet creation:** How is a tweet stored and what happens immediately after posting?
2. **Timeline generation:** How does a user see tweets from people they follow? (Fan-out on write vs Fan-out on read)
3. **Search:** How would you implement full-text search on tweets?
4. **Trending topics:** How do you calculate trending hashtags in real-time?
5. **Notifications:** How are real-time notifications delivered?
6. **At-scale challenges:** Twitter has celebrities with 100M followers. How does a celebrity tweet reach all followers?

Draw the complete architecture diagram and explain each component.

---

## STEP 9: Advanced Database Concepts

### 📖 Concept Explanation

### 📊 Database Indexes Deep Dive

```sql
-- B-Tree Index (default, good for range queries)
CREATE INDEX idx_orders_created_at ON orders(created_at);
-- SELECT * FROM orders WHERE created_at > '2024-01-01'  ← uses index

-- Composite Index (order matters!)
CREATE INDEX idx_orders_user_status ON orders(user_id, status);
-- SELECT * FROM orders WHERE user_id = 1 AND status = 'paid'  ← uses both
-- SELECT * FROM orders WHERE user_id = 1  ← uses index (leftmost prefix)
-- SELECT * FROM orders WHERE status = 'paid'  ← DOESN'T use index!

-- Partial Index (index only subset of rows)
CREATE INDEX idx_active_users ON users(email) WHERE is_active = TRUE;
-- Much smaller index, faster queries for active users

-- GIN Index for full-text search
CREATE INDEX idx_products_search ON products USING GIN(to_tsvector('english', name || ' ' || description));
-- SELECT * FROM products WHERE to_tsvector('english', name) @@ to_tsquery('laptop')
```

### 📊 EXPLAIN ANALYZE — Query Optimization

```sql
EXPLAIN ANALYZE
SELECT u.name, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE u.created_at > '2024-01-01'
GROUP BY u.id, u.name
ORDER BY order_count DESC
LIMIT 10;

-- Output shows:
-- Seq Scan vs Index Scan (Seq Scan on large tables = problem!)
-- rows=10000 (estimated) vs rows=9872 (actual) 
-- cost=0.00..1234.56 (higher = worse)
-- Nested Loop vs Hash Join vs Merge Join
```

### 📊 Elasticsearch for Full-Text Search

```python
from elasticsearch import Elasticsearch

es = Elasticsearch(['http://localhost:9200'])

# Index a document
es.index(index='products', id=product_id, document={
    'name': 'iPhone 15 Pro',
    'description': 'Latest Apple smartphone with titanium frame',
    'price': 999,
    'category': 'Electronics',
})

# Full-text search
results = es.search(index='products', body={
    'query': {
        'multi_match': {
            'query': 'apple smartphone',
            'fields': ['name^3', 'description'],  # name boosted 3x
            'fuzziness': 'AUTO'  # handles typos
        }
    },
    'filter': {
        'range': {'price': {'lte': 1000}}
    }
})
```

### 📝 Assignment 9

**Task:** Your e-commerce product search is slow:
- 10 million products
- Users search by keyword, category, price range, rating
- Currently using: `SELECT * FROM products WHERE name LIKE '%iphone%'` (very slow!)

1. Design a proper search solution using Elasticsearch
2. How do you keep Elasticsearch in sync with the main database?
3. Design the indexing strategy
4. What queries would you need? (keyword, filter, sort, pagination)

---

## 🏁 Advanced Level Complete!

**Concepts mastered:**
- ✅ CAP Theorem (CP vs AP trade-offs)
- ✅ Distributed Systems Fundamentals (consensus, consistency models, idempotency)
- ✅ Event-Driven Architecture (EDA, Event Sourcing, CQRS)
- ✅ Microservices (service discovery, Saga pattern, Strangler Fig)
- ✅ Kafka (deep dive, vs RabbitMQ, partitioning strategy)
- ✅ System Design Patterns (Circuit Breaker, Bulkhead, Retry, Sidecar)
- ✅ High Availability & Fault Tolerance (Active-Active, Chaos Engineering)
- ✅ Real-World Case Studies (Uber, Netflix, WhatsApp, URL Shortener, Twitter)
- ✅ Advanced Database Concepts (Indexes, Query Optimization, Elasticsearch)

**You are now ready to:**
- [ ] Tackle system design interviews at mid/senior level
- [ ] Design and build the three final projects
- [ ] Have intelligent discussions about architecture trade-offs
- [ ] Contribute to architecture decisions at work

**➡️ Next: FINAL_PROJECTS_README.md and PROJECT SOLUTIONS**
