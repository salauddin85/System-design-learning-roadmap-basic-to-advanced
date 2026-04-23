# 📁 System Design Training — Complete Folder Structure

```
/system-design-training/
│
├── 📘 README_BASIC.md
│   └── Steps 1–12: Client-server, APIs, HTTP/HTTPS, DNS,
│       Monolith vs Microservices, SQL vs NoSQL, Caching,
│       Load Balancers, Queues, Scalability, Availability
│
├── 📗 README_INTERMEDIATE.md
│   └── Steps 1–10: Horizontal/Vertical Scaling, DB Replication,
│       Sharding, Redis Deep Dive, Load Balancing Strategies,
│       REST API Best Practices, Rate Limiting, Celery,
│       Logging & Monitoring, Security, CDN, API Gateway
│
├── 📕 README_ADVANCED.md
│   └── Steps 1–9: CAP Theorem, Distributed Systems, Event-Driven
│       Architecture, Event Sourcing, CQRS, Microservices Patterns,
│       Kafka Deep Dive, Circuit Breaker, Bulkhead, High Availability,
│       Chaos Engineering, Case Studies (Uber/Netflix/WhatsApp/Twitter),
│       Elasticsearch, Database Indexes
│
├── 🏗️ FINAL_PROJECTS_README.md
│   └── All 3 project specs, architecture diagrams, setup instructions,
│       API designs, deployment guide, resume descriptions
│
├── projects/
│   │
│   ├── project1/                   🔗 SnapLink — URL Shortener
│   │   └── SCAFFOLD.py             Starter: models, settings, docker-compose
│   │
│   ├── project2/                   💬 ChatWave — Real-Time Chat
│   │   └── SCAFFOLD.py             Starter: models, ASGI config, WebSocket routing
│   │
│   └── project3/                   🛒 MarketFlow — E-Commerce Orders
│       └── SCAFFOLD.py             Starter: models, Celery config, docker-compose
│
└── solutions/
    │
    ├── PROJECT_1_SOLUTION.md       Full SnapLink solution:
    │                               DB schema, Base62 algorithm, Redis cache strategy,
    │                               async analytics pipeline, rate limiting, scaling plan,
    │                               failure handling, trade-offs
    │
    ├── PROJECT_2_SOLUTION.md       Full ChatWave solution:
    │                               WebSocket consumer, Redis Pub/Sub fanout, presence system,
    │                               FCM push notifications, Elasticsearch search,
    │                               S3 presigned uploads, scaling to 100k connections
    │
    └── PROJECT_3_SOLUTION.md       Full MarketFlow solution:
                                    Full DB schema, Redis cart (Hash structure),
                                    SELECT FOR UPDATE inventory locking,
                                    Redis Lua flash sale atomics, Elasticsearch search,
                                    Saga pattern, Celery task routing, failure handling
```

---

## 📚 Recommended Learning Order

```
Week 1-2: README_BASIC.md
  → Complete all 12 assignments
  → Build the URL Shortener capstone from Assignment 12

Week 3-4: README_INTERMEDIATE.md
  → Complete all 10 assignments
  → Build the Food Delivery capstone from the Intermediate final assignment

Week 5-6: README_ADVANCED.md
  → Complete all 9 assignments
  → Study all 4 case studies deeply

Week 7-8: PROJECT 1 — SnapLink
  → Read FINAL_PROJECTS_README.md project 1 spec
  → Build from scratch using SCAFFOLD.py
  → Check PROJECT_1_SOLUTION.md when stuck

Week 9-10: PROJECT 2 — ChatWave
  → Build from scratch using SCAFFOLD.py
  → Check PROJECT_2_SOLUTION.md when stuck

Week 11-12: PROJECT 3 — MarketFlow
  → Most complex — build incrementally: catalog → cart → orders → payments
  → Check PROJECT_3_SOLUTION.md when stuck

Week 13: Polish
  → Write proper READMEs for all 3 GitHub repos
  → Deploy at least one project (Render/Railway/EC2)
  → Update LinkedIn and CV with resume descriptions from FINAL_PROJECTS_README.md
```

---

## 🎯 Interview Readiness Checklist

After completing this training, you should be able to answer:

### Basic (L1-L2 interviews)
- [ ] Explain what happens when you type a URL in a browser
- [ ] What is the difference between SQL and NoSQL? When do you use each?
- [ ] What is caching? What are the different types?
- [ ] What is a load balancer and why do we need one?
- [ ] What is the difference between monolith and microservices?

### Intermediate (L3-L4 interviews)
- [ ] How do you scale a Django application to handle 10x traffic?
- [ ] Design an API rate limiting system
- [ ] How does session management work in a horizontally scaled system?
- [ ] What is database replication? What is sharding?
- [ ] How would you implement a background job system?
- [ ] Design the caching layer for a product catalog

### Advanced (L5-L6 / Senior interviews)
- [ ] Explain the CAP theorem with examples
- [ ] Design a real-time messaging system at scale
- [ ] How would you prevent overselling in an e-commerce flash sale?
- [ ] Explain the Circuit Breaker pattern and when you'd use it
- [ ] Design a URL shortener that handles 10,000 requests/second
- [ ] Explain eventual consistency and when it's acceptable
- [ ] How does Kafka differ from a regular message queue?
- [ ] Design a system like Uber's ride matching at scale

---

## 🏆 Final Words

System design is a skill built through:
1. **Understanding concepts** (this training covers that)
2. **Building real systems** (the 3 projects cover that)
3. **Reading about real systems** (case studies + engineering blogs)
4. **Practice communicating designs** (mock interviews)

**Recommended blogs to follow:**
- engineering.atspotify.com
- netflixtechblog.com
- eng.uber.com
- engineering.linkedin.com
- discord.com/blog/engineering
- shopify.engineering

Good luck, Salauddin! 🚀
