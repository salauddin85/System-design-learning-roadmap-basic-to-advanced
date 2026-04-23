# 📘 System Design Training — BASIC LEVEL
### For Intern Developers with Zero System Design Knowledge

---

## 🧭 Introduction

Welcome! This is your starting point.

Before you can design systems used by millions of people, you need to understand the building blocks. This README will walk you through every fundamental concept — step by step, with real-world examples and hands-on assignments.

Think of system design like building a city:
- You need roads (networking)
- Power grids (servers)
- Post offices (APIs)
- Traffic rules (protocols)
- Maps (DNS)

By the end of this module, you'll understand how the internet works, how software talks to other software, and how to think about building reliable systems.

---

## ✅ Prerequisites

- Basic understanding of programming (any language is fine)
- Know what a "website" is from a user's perspective
- Willingness to learn and think logically

---

## 🗺️ Learning Roadmap

---

## STEP 1: What is System Design?

### 📖 Concept Explanation

System design is the process of defining the **architecture, components, and interactions** of a system to satisfy specific requirements.

In simple terms: **How do you build software that works well for many people, doesn't crash, and is fast?**

When a company like Facebook says "design a chat system for 1 billion users," they want you to think about:
- How will you store billions of messages?
- How will messages be delivered in milliseconds?
- What happens if one server goes down?

System design is split into two types:

**1. High-Level Design (HLD):** The big picture — what components exist and how they connect.

**2. Low-Level Design (LLD):** The details — how each component is coded internally.

As an intern/junior developer, you'll mostly focus on HLD first.

### 🌍 Real-World Example

When you open Instagram and see posts from people you follow, behind the scenes:
1. Your phone sent a request to Instagram's servers
2. Servers fetched your following list from a database
3. Posts were fetched, ranked, and returned
4. Your app displayed them

All of this happened in under 1 second. THAT is the result of good system design.

### 📊 Diagram

```
[User's Phone]
     |
     | (sends request)
     v
[Instagram Servers]
     |
     | (fetches data)
     v
[Database / Cache]
     |
     v
[Returns Posts]
     |
     v
[User sees their feed]
```

### ✅ Best Practices

- Always understand the REQUIREMENTS before designing
- Ask "what could go wrong?" at every step
- Think in components: don't see the system as one big blob
- Always consider: performance, reliability, scalability, cost

### ❌ Common Mistakes

- Jumping to solutions before understanding the problem
- Ignoring failure scenarios (what if a server crashes?)
- Over-engineering simple systems
- Under-engineering systems that need to scale

### 📝 Assignment 1

**Task:** Think of any app you use daily (e.g., WhatsApp, YouTube, Pathao).

Write a simple paragraph answering:
1. What does the app do?
2. Who are the users?
3. What data does the app store?
4. What happens if the app's server goes down?
5. How many people use the app at once?

**Goal:** Learn to ask the right questions before designing anything.

---

## STEP 2: Client-Server Architecture

### 📖 Concept Explanation

This is the most fundamental model of how computers communicate.

**Client:** The device/software that asks for something (your phone, browser, app)
**Server:** The computer that responds to requests and provides data

Think of it like a restaurant:
- You (client) sit at a table and order food
- The kitchen (server) prepares it and gives it to you
- You don't cook — you request, they serve

A server is just a computer (usually a powerful one) that runs 24/7, waiting for requests and responding to them.

### 🌍 Real-World Example

When you visit `https://google.com`:
- Your browser = CLIENT
- Google's computers = SERVER
- You type a query → browser sends request → Google responds with results

### 📊 Diagram

```
CLIENT                         SERVER
+--------+    Request -----> +----------+
|        |                   |          |
| Browser|                   | Google's |
| or App |                   | Computer |
|        |    <----- Response|          |
+--------+                   +----------+
```

**Types of clients:**
- Web browser (Chrome, Firefox)
- Mobile app (Android/iOS)
- Desktop app
- Another server (server-to-server communication)

**Types of servers:**
- Web server (serves HTML pages)
- API server (serves data)
- Database server (stores data)
- File server (stores files/images)

### ✅ Best Practices

- Clients should never directly access the database — always go through a server
- Servers should be stateless (don't remember who you are — store that in a database or token)
- Never trust data from the client — always validate on the server

### ❌ Common Mistakes

- Storing sensitive data on the client
- Letting clients directly call the database
- Making the server do too much at once

### 📝 Assignment 2

**Task:** Draw (on paper or use any tool) a simple client-server diagram for a food delivery app like Foodpanda:
1. What is the client?
2. What is the server?
3. What request does the client send when placing an order?
4. What does the server respond with?

---

## STEP 3: What is an API?

### 📖 Concept Explanation

**API = Application Programming Interface**

An API is a way for two pieces of software to talk to each other. It defines the rules for how to ask for something and what you'll get back.

Think of an API like a waiter in a restaurant:
- You (client) don't go to the kitchen directly
- The waiter (API) takes your order, goes to the kitchen, and brings back your food
- You follow a "menu" — you can only order what's on it

On the web, APIs are usually **REST APIs** which use HTTP (the language of the internet).

**A REST API works with:**
- **URL (Endpoint):** The address to call (like `/api/users`)
- **HTTP Method:** What you want to do (GET = read, POST = create, PUT = update, DELETE = remove)
- **Request Body:** Data you send (usually JSON format)
- **Response:** Data you get back (usually JSON)

### 🌍 Real-World Example

When Pathao's app shows you nearby drivers, it calls an API like:

```
GET https://api.pathao.com/drivers/nearby?lat=23.8103&lng=90.4125
```

The server responds with:
```json
{
  "drivers": [
    {"id": "D123", "name": "Rahim", "distance": "0.5km"},
    {"id": "D456", "name": "Karim", "distance": "0.8km"}
  ]
}
```

### 📊 Diagram

```
Mobile App                API Server               Database
+----------+   GET /drivers  +----------+  Query   +----------+
|          | --------------> |          | -------> |          |
| Pathao   |                 | Backend  |          | Driver   |
| App      | <-------------- | Server   | <------- | Data     |
|          |  JSON Response  |          |  Result  |          |
+----------+                 +----------+          +----------+
```

**Common HTTP Methods:**
| Method | Purpose | Example |
|--------|---------|---------|
| GET | Read data | Get user profile |
| POST | Create data | Register new user |
| PUT | Update all fields | Update entire profile |
| PATCH | Update some fields | Change just email |
| DELETE | Delete data | Remove account |

**HTTP Status Codes:**
| Code | Meaning |
|------|---------|
| 200 | OK - Success |
| 201 | Created - New resource made |
| 400 | Bad Request - Your request was wrong |
| 401 | Unauthorized - Login first |
| 403 | Forbidden - You don't have permission |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error - Server crashed |

### ✅ Best Practices

- Use proper HTTP methods (don't use GET to delete things!)
- Return meaningful status codes
- Version your APIs: `/api/v1/users` (so changes don't break old clients)
- Always validate inputs

### ❌ Common Mistakes

- Using GET requests that modify data
- Returning `200 OK` even when something failed
- Not handling errors properly
- Exposing sensitive data in API responses

### 📝 Assignment 3

**Task:** Design the API endpoints (URL, Method, Request, Response) for a simple Blog application with:
1. Create a new blog post
2. Get all blog posts
3. Get one specific blog post
4. Update a blog post
5. Delete a blog post

Format each like:
```
Method: POST
Endpoint: /api/posts
Request Body: { "title": "...", "content": "..." }
Response: { "id": 1, "title": "...", "created_at": "..." }
```

---

## STEP 4: HTTP/HTTPS Basics

### 📖 Concept Explanation

**HTTP = HyperText Transfer Protocol**

HTTP is the language that browsers and servers use to communicate. Every time you visit a website, your browser sends an HTTP request and the server sends an HTTP response.

Think of HTTP like sending letters:
- You write a letter (request) with your address and what you want
- The post office (internet) delivers it
- The receiver (server) reads it and sends a reply

**HTTPS = HTTP + Security (S = Secure)**

HTTPS encrypts the communication so no one in the middle can read it. This is critical for passwords, payment info, etc.

### 📊 HTTP Request Structure

```
GET /api/users/123 HTTP/1.1          ← Request Line (Method + URL + Version)
Host: api.example.com                 ← Headers (metadata)
Authorization: Bearer abc123          ← Auth token
Content-Type: application/json        ← What format we're sending
Accept: application/json              ← What format we want back
                                      ← (blank line separates headers from body)
{                                     ← Body (only for POST, PUT, PATCH)
  "name": "Salauddin"
}
```

### 📊 HTTP Response Structure

```
HTTP/1.1 200 OK                       ← Status Line
Content-Type: application/json        ← Response Headers
X-Request-Id: xyz789
                                      ← Blank line
{                                     ← Response Body
  "id": 123,
  "name": "Salauddin",
  "email": "sal@example.com"
}
```

### 🌍 HTTPS in Real World

When you buy something on Daraz:
- Without HTTPS: Your credit card number travels as plain text → hackers can steal it
- With HTTPS: Your card number is encrypted → even if intercepted, it looks like random gibberish

**How HTTPS works (simplified):**
1. Your browser says "I want to connect securely"
2. Server sends its SSL/TLS certificate (like an ID card)
3. Both sides agree on an encryption key
4. All communication is now encrypted

```
Browser                     Server
   |                           |
   |-- "Hello, I want HTTPS" ->|
   |                           |
   |<-- "Here's my certificate"|
   |                           |
   |-- "Here's my public key" ->|
   |                           |
   |<--- "Encryption agreed" --|
   |                           |
   |=== Encrypted Traffic ====|
```

### ✅ Best Practices

- ALWAYS use HTTPS in production, never HTTP
- Set proper headers (Content-Type, Cache-Control, etc.)
- Use HSTS (HTTP Strict Transport Security) to force HTTPS
- Keep SSL certificates up to date

### ❌ Common Mistakes

- Serving APIs over HTTP (insecure)
- Ignoring headers (they carry critical metadata)
- Not understanding status codes

### 📝 Assignment 4

**Task:** Using a tool like `curl` or Postman (or even your browser's developer tools):
1. Open any public API (e.g., `https://jsonplaceholder.typicode.com/posts/1`)
2. Inspect the request headers
3. Inspect the response headers and status code
4. Write down: What did you send? What did you receive?

**Bonus:** Try accessing the same URL with `http://` instead of `https://` — what happens?

---

## STEP 5: DNS — Domain Name System (VERY IMPORTANT)

### 📖 Concept Explanation

DNS is like the **phone book of the internet**.

Every website has an IP address (like `142.250.185.46`), but humans can't remember those. DNS translates human-readable domain names like `google.com` into IP addresses that computers can use.

Think of it like this:
- You know your friend's name: "Ahmed"
- You don't remember his phone number
- You look him up in your contacts (DNS) → get his number (IP address)
- You call him (connect to the server)

### 🌍 What Happens When You Type a URL in Browser

This is one of the most famous system design interview questions. Let's break it down:

**URL typed:** `https://www.google.com/search?q=system+design`

**Step 1: Browser Cache Check**
- Browser checks if it already knows the IP for `google.com`
- If cached (saved recently), uses that IP directly

**Step 2: OS Cache Check**
- If browser doesn't know, it asks the OS (Windows/Linux/Mac)
- OS checks its own DNS cache

**Step 3: Router Check**
- If OS doesn't know, it asks your home/office router
- Router may have a cached answer

**Step 4: ISP DNS Server**
- If nobody local knows, your ISP (Grameenphone/Robi/BTCL) has a DNS server
- Your router asks this server

**Step 5: Recursive DNS Resolution**
- If ISP's DNS doesn't know, it goes through a chain:

```
Your Browser
     |
     v
ISP DNS Server (Resolver)
     |
     v (if not cached)
Root DNS Server  ("I don't know google.com, but I know who handles .com")
     |
     v
.com TLD Server  ("I don't know google.com specifically, but google.com is managed by Google's nameserver")
     |
     v
Google's Authoritative DNS Server  ("google.com IP is 142.250.185.46")
     |
     v
Back to ISP → Back to your browser
```

**Step 6: TCP Connection**
- Browser now has the IP: `142.250.185.46`
- Browser initiates a TCP connection (3-way handshake)

**Step 7: TLS Handshake (for HTTPS)**
- Browser and server agree on encryption

**Step 8: HTTP Request**
- Browser sends: `GET /search?q=system+design HTTP/1.1`

**Step 9: Server Processes Request**
- Google's load balancer receives the request
- Routes to an available server
- Server processes the search query
- Fetches results from its databases

**Step 10: HTTP Response**
- Server sends back HTML/JSON

**Step 11: Browser Renders**
- Browser parses HTML, fetches CSS/JS/images
- Displays the page to you

### 📊 DNS Record Types

| Record | Purpose | Example |
|--------|---------|---------|
| A | Maps domain to IPv4 | `google.com → 142.250.185.46` |
| AAAA | Maps domain to IPv6 | `google.com → 2001:db8::1` |
| CNAME | Alias to another domain | `www.google.com → google.com` |
| MX | Mail server for domain | Email routing |
| TXT | Verification text | Domain ownership proof |
| NS | Name server for domain | Who handles DNS for this domain |

### 📊 Full Diagram

```
[Browser] → types: google.com
    |
    | Step 1: Check browser cache? No
    | Step 2: Check OS cache? No
    | Step 3: Check router? No
    v
[ISP DNS Resolver]
    |
    | Step 4: Check cache? No, go find it
    v
[Root DNS Server]   → "Try .com TLD server"
    |
    v
[.com TLD Server]   → "Try Google's DNS server"
    |
    v
[Google's DNS Server] → "142.250.185.46!"
    |
    v
[ISP Resolver caches + returns to browser]
    |
    v
[Browser connects to 142.250.185.46]
    |
    v
[Google Server responds with HTML]
    |
    v
[Browser renders Google homepage]
```

### ✅ Best Practices

- Set appropriate DNS TTL (Time To Live) values — lower TTL means changes propagate faster but creates more DNS queries
- Use CDN with GeoDNS to route users to nearest servers
- Always configure both A records and AAAA (IPv6) records
- Use DNS load balancing for basic traffic distribution

### ❌ Common Mistakes

- Setting TTL too high (changes take hours to propagate)
- Forgetting to renew domain registration
- Not setting up proper MX records for email

### 📝 Assignment 5

**Task:** Using your terminal (or online tools like `https://mxtoolbox.com`):

1. Run: `nslookup google.com` — What IP does it return?
2. Run: `nslookup -type=MX google.com` — Who handles Google's email?
3. Run: `nslookup -type=NS google.com` — What are Google's nameservers?
4. Run: `nslookup facebook.com` — Different IP than Google?
5. Write a simple explanation (like you're explaining to a 10-year-old) of what DNS does.

---

## STEP 6: Monolith vs Microservices

### 📖 Concept Explanation

**Monolith Architecture:**
Everything is in one big application. The user authentication, product catalog, payment system, notifications — all in one codebase, deployed as one unit.

**Microservices Architecture:**
The application is split into small, independent services. Each service handles one specific function and runs separately.

**Analogy:**
- **Monolith** = A large department store where one company runs everything (clothing, food, electronics)
- **Microservices** = A shopping mall where each store is separate (Zara for clothes, KFC for food, Samsung for electronics)

### 📊 Comparison Diagram

```
MONOLITH
+----------------------------------------------+
|           Single Application                  |
|  +----------+ +----------+ +---------------+  |
|  |   Auth   | | Products | |   Payments    |  |
|  +----------+ +----------+ +---------------+  |
|  +----------+ +------------------------+      |
|  | Orders   | |    Notifications       |      |
|  +----------+ +------------------------+      |
+----------------------------------------------+
         |
         | Single deployment
         v
    [One Server]


MICROSERVICES
+----------+ +----------+ +----------+
|  Auth    | | Products | | Payments |
| Service  | | Service  | | Service  |
+----------+ +----------+ +----------+
     |            |            |
     v            v            v
 [Server 1]   [Server 2]   [Server 3]

Each service:
- Has its own database
- Deployed independently
- Can be scaled independently
- Communicates via APIs
```

### 🌍 Real-World Example

**Netflix** started as a monolith. As it grew to millions of users, they moved to microservices:
- `recommendation-service` → suggests what to watch
- `streaming-service` → handles video delivery
- `billing-service` → manages subscriptions
- `user-service` → handles accounts

Now if the recommendation system crashes, streaming still works!

### ✅ When to Use What

| Situation | Use |
|-----------|-----|
| Small team, early startup | Monolith |
| Rapid prototyping | Monolith |
| Large team, complex product | Microservices |
| Different scaling needs per feature | Microservices |
| High availability requirements | Microservices |

### ✅ Best Practices

- Start with a monolith, migrate to microservices when needed
- Each microservice should have a single responsibility
- Microservices should communicate via APIs (REST or message queues)
- Each microservice should have its own database

### ❌ Common Mistakes

- Building microservices too early (premature optimization)
- Microservices sharing a single database (defeats the purpose)
- Too many tiny services (microservices hell)
- Not considering the network overhead between services

### 📝 Assignment 6

**Task:** You're building a social media platform like Twitter.

1. Draw the monolith architecture (list all components in one box)
2. Draw the microservices architecture (separate services)
3. List 3 reasons why Twitter would prefer microservices
4. List 2 downsides of going microservices for a new startup

---

## STEP 7: Database Basics — SQL vs NoSQL

### 📖 Concept Explanation

**What is a Database?**
A database is an organized collection of data. It's where your application stores everything — users, products, orders, messages.

**SQL Databases (Relational):**
Data is stored in tables with rows and columns, like a spreadsheet. Tables can relate to each other. Uses Structured Query Language (SQL) to query data.

Examples: PostgreSQL, MySQL, SQLite, Oracle

**NoSQL Databases (Non-relational):**
Data is stored in flexible formats — documents (JSON), key-value pairs, graphs, or columns. Good for unstructured or rapidly changing data.

Examples: MongoDB (documents), Redis (key-value), Cassandra (wide-column), Neo4j (graph)

### 📊 SQL Example

```
USERS table:
+----+----------+-------------------+------------+
| id | name     | email             | created_at |
+----+----------+-------------------+------------+
|  1 | Rahim    | rahim@email.com   | 2024-01-01 |
|  2 | Karim    | karim@email.com   | 2024-01-05 |
+----+----------+-------------------+------------+

ORDERS table:
+----+---------+--------+--------+
| id | user_id | amount | status |
+----+---------+--------+--------+
|  1 |       1 | 500.00 | paid   |
|  2 |       1 | 200.00 | pending|
+----+---------+--------+--------+

Query to get Rahim's orders:
SELECT * FROM orders WHERE user_id = 1;
```

### 📊 NoSQL (MongoDB) Example

```json
{
  "_id": "user_001",
  "name": "Rahim",
  "email": "rahim@email.com",
  "orders": [
    {"amount": 500.00, "status": "paid"},
    {"amount": 200.00, "status": "pending"}
  ],
  "preferences": {
    "theme": "dark",
    "language": "bn"
  }
}
```

### 🌍 Real-World Usage

| Company | Database | Why |
|---------|----------|-----|
| Bank | PostgreSQL | Financial data needs strict relations + ACID |
| Instagram | PostgreSQL + Cassandra | Photos metadata in SQL, feeds in NoSQL |
| Netflix | Cassandra | Massive scale, high write speed needed |
| Twitter | MySQL + Redis | SQL for tweets, Redis for cache/timelines |

### ✅ When to Use SQL vs NoSQL

**Use SQL when:**
- Data has clear relationships (users → orders → products)
- You need complex queries (JOINs)
- Data integrity is critical (banking, healthcare)
- ACID compliance is required

**Use NoSQL when:**
- Data structure changes frequently
- Huge amounts of unstructured data
- Need massive horizontal scaling
- Simple lookups (no complex JOINs)
- Real-time, high-speed reads/writes

### ✅ Best Practices

- Normalize your SQL schema (avoid data duplication)
- Index your frequently queried columns
- Use the right database for the right job — it's okay to use both
- Always back up your database

### ❌ Common Mistakes

- Using NoSQL because it's "trendy" without a real reason
- Not using indexes (causes slow queries)
- Storing everything in one massive table
- Not planning for data growth

### 📝 Assignment 7

**Task:** Design a database schema for an e-commerce platform:

1. **SQL Design:** Create tables for Users, Products, Orders, and OrderItems. Show the columns and relationships.

2. **NoSQL Design:** Show how the same data would look as a MongoDB document.

3. **Answer:** For an e-commerce platform, which would you prefer and why?

---

## STEP 8: What is Caching?

### 📖 Concept Explanation

**Caching** is storing a copy of frequently accessed data in a faster location so future requests can be served faster.

**Analogy:** 
You're a student preparing for exams. Instead of going to the library (slow) every time you need a formula, you write it on a sticky note (cache) on your desk. Much faster!

- **Cache hit:** The data you need is in the cache → serve it immediately (fast!)
- **Cache miss:** The data isn't in the cache → go fetch it from the real source (slow), then store it in cache

**Types of Caching:**

1. **Browser Cache:** Your browser saves CSS, images, JS locally
2. **CDN Cache:** A server network that caches content close to users globally
3. **Application Cache:** Your backend caches frequent database queries
4. **Database Cache:** Database stores frequently accessed query results

### 📊 Diagram

```
Without Cache:
User → App Server → Database → (slow processing) → Response

With Cache:
User → App Server → Cache HIT? → Yes → Return immediately ✅
                              → No  → Database → Store in Cache → Return
```

### 🌍 Real-World Example

**YouTube video thumbnails:**
- Thumbnails are fetched from YouTube's origin servers and cached on CDN servers around the world
- When you load YouTube in Dhaka, the thumbnail comes from a server in Singapore (or Mumbai), not California
- This makes it load in milliseconds instead of seconds

**Redis caching example:**
```python
# Without cache (slow - hits database every time)
def get_user(user_id):
    return db.query("SELECT * FROM users WHERE id = ?", user_id)

# With Redis cache (fast)
def get_user(user_id):
    cached = redis.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)  # Cache HIT - instant!
    
    user = db.query("SELECT * FROM users WHERE id = ?", user_id)
    redis.setex(f"user:{user_id}", 3600, json.dumps(user))  # Cache for 1 hour
    return user
```

### ✅ Cache Invalidation Strategies

| Strategy | How it Works | Use Case |
|----------|-------------|---------|
| TTL (Time-to-Live) | Cache expires after set time | User profiles, product listings |
| Cache-aside | App manages cache manually | Most common pattern |
| Write-through | Write to cache AND DB at same time | When freshness is critical |
| Write-back | Write to cache first, DB later | High-write scenarios |

### ✅ Best Practices

- Cache data that is read often and changes rarely
- Always set an expiry (TTL) on cached items
- Cache at the right level (CDN vs App vs DB)
- Monitor cache hit rate (aim for 80%+)

### ❌ Common Mistakes

- Caching everything (wastes memory, stale data issues)
- Not setting TTL (data becomes stale forever)
- Not handling cache misses gracefully
- Forgetting to invalidate cache when data changes

### 📝 Assignment 8

**Task:** A news website gets 10,000 requests/minute for its homepage.

1. Without caching, what problem would this cause?
2. Design a caching strategy for the homepage
3. How long should the homepage be cached? (the news updates every 5 minutes)
4. What is the cache key you would use?
5. What happens when a new article is published? (cache invalidation)

---

## STEP 9: What is a Load Balancer?

### 📖 Concept Explanation

A **Load Balancer** distributes incoming network traffic across multiple servers so no single server gets overwhelmed.

**Analogy:** 
A bank has 5 tellers. Instead of everyone lining up at teller #1, a manager (load balancer) directs each customer to the next available teller. Work is distributed evenly.

**Why do we need it?**
- One server can only handle so many requests
- If that one server crashes → your entire app goes down
- Load balancing enables horizontal scaling (adding more servers)

### 📊 Diagram

```
         Incoming Traffic
              |
              v
      +---------------+
      |  Load Balancer |
      +---------------+
       /       |      \
      v        v       v
  +------+ +------+ +------+
  |Server| |Server| |Server|
  |  #1  | |  #2  | |  #3  |
  +------+ +------+ +------+
      \        |       /
       v       v      v
          [Database]
```

### 🌍 Load Balancing Algorithms

| Algorithm | How It Works | Best For |
|-----------|-------------|---------|
| Round Robin | Each request goes to next server in order | Equal-capacity servers |
| Least Connections | Send to server with fewest active connections | Different-length requests |
| IP Hash | Same client always goes to same server | Session-based apps |
| Weighted Round Robin | Powerful servers get more traffic | Different-capacity servers |

### 🌍 Real-World Example

**Amazon during Black Friday:**
- Millions of people shopping at once
- One server would crash instantly
- Amazon uses load balancers to distribute traffic across thousands of servers
- If one server crashes, load balancer stops sending traffic to it

**Popular Load Balancers:**
- **Nginx** (free, open-source — most popular)
- **HAProxy** (free, very performant)
- **AWS ALB/NLB** (managed cloud service)
- **AWS ELB** (Amazon's Elastic Load Balancer)

### 📊 Nginx Load Balancer Config (Simple Example)

```nginx
upstream backend {
    server 192.168.1.1:8000;
    server 192.168.1.2:8000;
    server 192.168.1.3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://backend;
    }
}
```

### ✅ Best Practices

- Always have health checks — load balancer should stop sending traffic to unhealthy servers
- Use at least 2 load balancers (for redundancy)
- Enable SSL termination at the load balancer
- Log and monitor traffic at the load balancer level

### ❌ Common Mistakes

- Single point of failure (only one load balancer)
- Not setting up health checks
- Load balancing without session management (users getting logged out)

### 📝 Assignment 9

**Task:** An online exam platform expects 5,000 students to take an exam simultaneously.

1. Why would a single server struggle?
2. Design a load-balanced setup with 3 servers
3. Which load balancing algorithm would you choose and why?
4. What happens if one of the 3 servers crashes during the exam?
5. How does the load balancer detect the crashed server?

---

## STEP 10: Introduction to Message Queues

### 📖 Concept Explanation

A **Message Queue** is a way for services to communicate asynchronously by passing messages through a queue (like a waiting line).

**Without a queue (synchronous):**
- Customer orders food → Chef cooks IMMEDIATELY → Customer waits staring at the chef
- If chef is busy, customer waits and waits…

**With a queue (asynchronous):**
- Customer orders food → Order goes on a ticket board (queue) → Customer sits down
- Chef picks up tickets one by one, in order
- Customer gets a notification when food is ready

### 📊 Diagram

```
Producer                  Queue                 Consumer
(Service A)           (Message Broker)         (Service B)
    |                      |                       |
    |--send message ------->|                       |
    |                      |                       |
    |  (continues working) |                       |
    |                      |--deliver message----->|
    |                      |                       |
    |                      |    (B processes it)   |
    |                      |                       |
    |<------(eventually) result back --------------|
```

### 🌍 Real-World Example

**Email after placing an order on Daraz:**
1. You place an order (Daraz's API handles it instantly)
2. Daraz's API puts a "send confirmation email" message in a queue
3. API responds to you immediately (order placed!)
4. A separate email service picks up messages from the queue
5. Emails are sent one by one

Without a queue: Daraz's API would be waiting for the email to send before confirming your order (slow!)

**Popular Message Queues:**
- **Redis** (simple, fast, lightweight)
- **RabbitMQ** (feature-rich, reliable)
- **Apache Kafka** (massive scale, millions of messages/sec)
- **AWS SQS** (managed, easy to use)
- **Celery** (Python background task framework, often with Redis/RabbitMQ)

### ✅ Best Practices

- Use queues for tasks that don't need an immediate response (emails, reports, notifications)
- Ensure your consumer can handle retries (if processing fails)
- Monitor queue size — a growing queue = consumer can't keep up
- Use dead-letter queues for failed messages

### ❌ Common Mistakes

- Using queues for tasks that NEED immediate responses
- Not handling failed messages (they disappear!)
- Not monitoring queue depth

### 📝 Assignment 10

**Task:** An e-commerce platform needs to:
- Send order confirmation email
- Update inventory in a warehouse system
- Generate an invoice PDF
- Send an SMS to the customer

1. Which of these should use a message queue? Why?
2. Draw a simple diagram showing how the queue fits in
3. What happens if the email service is down? (How does a queue help?)

---

## STEP 11: Introduction to Scalability

### 📖 Concept Explanation

**Scalability** is a system's ability to handle growing amounts of work by adding resources.

Two types:

**1. Vertical Scaling (Scale Up):**
Make one machine more powerful — add more CPU, RAM, storage.

```
Before: [Server with 4 CPU, 16GB RAM]
After:  [Server with 32 CPU, 128GB RAM]
```

**Analogy:** Buy a bigger truck to carry more cargo.

**2. Horizontal Scaling (Scale Out):**
Add more machines.

```
Before: [Server 1]
After:  [Server 1] [Server 2] [Server 3] [Server 4]
```

**Analogy:** Use many smaller trucks instead of one big one.

| | Vertical | Horizontal |
|---|---------|-----------|
| Cost | Expensive (high-end hardware) | Cheaper (commodity hardware) |
| Limit | Hardware limits exist | Almost unlimited |
| Downtime | Requires restart | No downtime |
| Complexity | Simple | Requires load balancers, coordination |
| Used By | Small apps, databases | Large web apps |

### 🌍 Real-World Example

**YouTube's growth:**
- 2005: Small servers, few users
- Today: 500 hours of video uploaded EVERY MINUTE
- Solution: Thousands of servers horizontally scaled
- Some critical databases are still vertically scaled (expensive but necessary)

### ✅ Best Practices

- Design for horizontal scaling from the start (stateless services)
- Use auto-scaling in cloud (AWS Auto Scaling, Kubernetes HPA)
- Don't prematurely optimize — scale when needed

### ❌ Common Mistakes

- Vertical scaling as a long-term solution (there's a limit)
- Stateful servers (hard to horizontally scale)

### 📝 Assignment 11

**Task:** A startup launches an app with 100 users. Over 6 months, they grow to 1 million users.

1. What happens to a single server as users grow?
2. At what point would you add horizontal scaling?
3. Design a horizontally scaled backend for 1 million users
4. What challenges come with horizontal scaling? (Hint: sessions, data consistency)

---

## STEP 12: Introduction to Availability

### 📖 Concept Explanation

**Availability** is the percentage of time a system is operational and accessible.

```
Availability = (Total Time - Downtime) / Total Time × 100%
```

**The "Nines" of availability:**

| Availability | Downtime per year | Example |
|-------------|------------------|---------|
| 99% (2 nines) | 3.65 days | Acceptable for non-critical apps |
| 99.9% (3 nines) | 8.77 hours | Most web apps target this |
| 99.99% (4 nines) | 52.6 minutes | E-commerce, banking |
| 99.999% (5 nines) | 5.26 minutes | Hospitals, emergency services |

Achieving five 9s is extremely difficult and expensive.

**How to improve availability:**
- Remove single points of failure (have redundancy)
- Use load balancers
- Use multiple data centers
- Implement health checks and auto-restart
- Have a proper backup and recovery plan

### 🌍 Real-World Example

**AWS S3 advertises 99.999999999% (11 nines) durability for data.**
**But even AWS has had outages** — availability is about design + process, not just claims.

**Single Point of Failure (SPOF) example:**
```
Bad design:
[Users] → [One Server] → [One Database]
          ↑                ↑
     SPOF - if it dies,  SPOF - if it dies,
     app is down         all data is gone!

Good design:
[Users] → [Load Balancer] → [Server 1]  ┐
                           → [Server 2]  ├→ [Primary DB] → [Replica DB]
                           → [Server 3]  ┘
```

### ✅ Best Practices

- Eliminate single points of failure
- Use redundancy at every layer
- Test your failure scenarios (chaos engineering)
- Have rollback plans for deployments

### ❌ Common Mistakes

- Assuming servers never fail (they always do eventually!)
- Not testing disaster recovery plans
- Treating availability as a "we'll fix it later" problem

### 📝 Assignment 12 (Final Basic Assignment)

**Capstone Task:** Design a high-level architecture for a simple URL shortener (like bit.ly):

Include:
1. API design (endpoints for creating and redirecting short URLs)
2. Database design (what data to store)
3. Caching strategy (which data to cache and why)
4. Basic load balancing setup
5. List 2 potential failure points and how to handle them

Draw a simple architecture diagram.

---

## 🏁 Basic Level Complete!

**Concepts covered:**
- ✅ What is System Design?
- ✅ Client-Server Architecture
- ✅ What is an API?
- ✅ HTTP/HTTPS Basics
- ✅ DNS (Domain Name System)
- ✅ What Happens When You Type a URL
- ✅ Monolith vs Microservices
- ✅ Database Basics (SQL vs NoSQL)
- ✅ What is Caching?
- ✅ What is a Load Balancer?
- ✅ Introduction to Message Queues
- ✅ Introduction to Scalability
- ✅ Introduction to Availability

**Before moving to Intermediate Level, ensure you can:**
- [ ] Explain client-server model without notes
- [ ] Design a basic REST API for any simple app
- [ ] Explain DNS resolution step-by-step
- [ ] Compare SQL vs NoSQL and choose the right one
- [ ] Draw a basic architecture with load balancer + cache + database
- [ ] Explain why caching matters
- [ ] Explain availability and the concept of "nines"

**➡️ Next: README_INTERMEDIATE.md**
