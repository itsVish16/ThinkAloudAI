import json
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

STANDARD_HLD_QUESTIONS = [
    # -------------------------------------------------------------------------
    # 1. Rate Limiter
    # -------------------------------------------------------------------------
    {
        "title": "Design a Distributed Rate Limiter",
        "product_target": "Cloudflare / AWS WAF / Stripe API Gateway",
        "category": "Core Infrastructure & Security",
        "difficulty": "Medium",
        "role": "Software Engineer / Senior Backend Engineer",
        "summary": "Design a distributed, low-latency API Rate Limiter to protect microservices from API abuse, DDoS attacks, brute-force requests, and resource starvation.",
        "functional_reqs": [
            "Limit requests based on Client IP, User ID, or API Key (e.g., 100 requests per minute per IP).",
            "Return HTTP status code 429 (Too Many Requests) with rate limit headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`).",
            "Support tiered rate limits for different user tiers (Free vs Tier 1 vs Enterprise) and endpoint-specific rules."
        ],
        "non_functional_reqs": [
            "Sub-millisecond processing latency (< 1ms P99 overhead per check).",
            "High availability with graceful fail-open fallback if rate limiting cluster degrades.",
            "Accurate distributed tracking across multi-region edge gateways.",
            "Low memory footprint across millions of active clients."
        ],
        "estimations": """- **Total Traffic:** 100,000 API requests/sec peak across global gateways.
- **Active Clients:** 10M active API keys/day.
- **Memory Footprint:** 10M keys * 64 bytes per Redis token bucket state = **~640 MB RAM** (fits easily in in-memory Redis cluster).
- **Network Bandwidth:** Rate check payload ~100 bytes * 100k QPS = **10 MB/sec**.""",
        "architecture_diagram": """```mermaid
flowchart TD
    Client[Client / Mobile App] -->|HTTP Request| CDN[Cloudflare CDN / Edge WAF]
    CDN --> LB[Global Load Balancer]
    LB --> Gateway[API Gateway / Envoy Reverse Proxy]
    
    Gateway -->|1. Run Rate Check Lua Script| RedisCluster[(Redis Cluster - Multi-Replica)]
    RedisCluster -->|2. Allowed (Tokens Remaining: 84)| Gateway
    Gateway -->|3. Forward Request| Backend[Backend Microservices]
    
    Gateway -.->|Tokens Depleted| 429Err[HTTP 429 Too Many Requests]
    Gateway -.->|Redis Timeout Fallback| FailOpen[Fail-Open: Forward & Alert Datadog]
```""",
        "data_model": """### In-Memory Storage Model (Redis)

**1. Token Bucket Redis Hash:**
```redis
HSET ratelimit:user_1024 tokens 95 last_refill 1718901234
EXPIRE ratelimit:user_1024 3600
```

**2. Sliding Window Log in Redis Sorted Set (ZSET):**
```redis
ZADD ratelimit:ip_192.168.1.1 1718901234.500 "req_uuid_abc"
ZREMRANGEBYSCORE ratelimit:ip_192.168.1.1 -inf (current_time - 60)
ZCARD ratelimit:ip_192.168.1.1
```""",
        "workflow": """### Life of a Rate-Limited Request:
1. Client sends request `GET /api/v1/orders` with `Authorization: Bearer <API_KEY>`.
2. API Gateway extracts client identifier (`user_id` or `IP`) and fetches matching rule (e.g. 100 req/min).
3. Gateway executes atomic **Lua Script** on Redis:
   - Computes tokens generated since `last_refill`.
   - If `tokens >= 1`: decrements token by 1, updates `last_refill`, and returns `ALLOWED`.
   - If `tokens < 1`: returns `REJECTED` along with estimated `Retry-After` seconds.
4. If allowed, request passes to backend. If rejected, Gateway immediately responds with `HTTP 429`.""",
        "deep_dive": """### Deep Dive & Engineering Trade-offs:
1. **Algorithm Comparison:**
   - **Token Bucket (Standard):** Supports bursts up to bucket capacity; memory efficient $O(1)$.
   - **Sliding Window Counter:** Blends rolling window accuracy with low memory, eliminating boundary burst vulnerabilities.
2. **Concurrency & Race Conditions:**
   - Multiple concurrent requests from the same user hitting different gateways cause read-modify-write races.
   - **Solution:** Execute rate-limiting logic inside Redis using **atomic Lua scripts** (`evalsha`), leveraging Redis single-threaded execution guarantees.
3. **Multi-Region Synchronization:**
   - Use local edge caches with centralized asynchronous Redis replication, or use consistent hashing to pin client IPs to specific regional gateway clusters."""
    },

    # -------------------------------------------------------------------------
    # 2. WhatsApp / WeChat
    # -------------------------------------------------------------------------
    {
        "title": "Design WhatsApp / Messenger (Real-Time Chat)",
        "product_target": "WhatsApp / Signal / Discord / Telegram",
        "category": "Real-Time Systems & Instant Messaging",
        "difficulty": "Hard",
        "role": "Senior Software Engineer / Distributed Systems SWE",
        "summary": "Design an end-to-end encrypted, real-time messaging system supporting 1-on-1 chats, group chats, message delivery receipts, online presence, and offline sync.",
        "functional_reqs": [
            "1-on-1 direct messaging and group chats (up to 1,000 members).",
            "Real-time message delivery receipts (Sent ✓, Delivered ✓✓, Read 🔵🔵).",
            "Online / offline presence tracking and typing indicators.",
            "Media sharing (photos, audio notes, video, documents).",
            "Automatic offline message queuing and synchronization upon reconnect."
        ],
        "non_functional_reqs": [
            "Real-time delivery latency (< 100ms P99).",
            "Zero message loss (At-least-once delivery with client-side deduplication).",
            "Guaranteed message ordering within individual conversations.",
            "High scalability: 500M Daily Active Users and 50M concurrent WebSocket connections."
        ],
        "estimations": """- **Daily Active Users (DAU):** 500M users.
- **Message Volume:** 500M * 100 messages/day = **50B messages/day $\\rightarrow$ ~600,000 messages/sec peak**.
- **Concurrent Connections:** **50M persistent WebSocket connections**.
- **Daily Storage:** 50B msgs * 200 bytes = **10 TB/day text**; Media (10% msgs with 1MB media) = **5 PB/day S3 storage**.""",
        "architecture_diagram": """```mermaid
flowchart TD
    UserA[User A Mobile App] <-->|Persistent WebSocket / TLS| WS1[Chat WebSocket Gateway 1]
    UserB[User B Mobile App] <-->|Persistent WebSocket / TLS| WS2[Chat WebSocket Gateway 2]
    
    WS1 -->|1. Lookup Recipient Session| SessionRegistry[(Redis Session Registry - user_id -> ws_ip)]
    WS1 -->|2. Publish Message Event| Kafka[Kafka / Pulsar Message Bus]
    
    Kafka --> MsgStorageWorker[Message Persistence Worker]
    MsgStorageWorker --> Cassandra[(Cassandra / ScyllaDB Message Store)]
    
    Kafka --> PushGateway[Push Notification Service - APNs / FCM]
    PushGateway -.->|If User B Offline| UserB
    
    Kafka --> WS2
    WS2 -->|3. Forward Message Packet| UserB
```""",
        "data_model": """### Cassandra / ScyllaDB Schema (Optimized for Fast Sequential Reads)

```sql
CREATE TABLE messages (
    conversation_id UUID,
    message_id TIMEUUID,                  -- Encodes millisecond timestamp & ensures chronological sorting
    sender_id UUID,
    content TEXT,
    media_url TEXT,
    delivery_status VARCHAR(10),          -- SENT, DELIVERED, READ
    created_at TIMESTAMP,
    PRIMARY KEY ((conversation_id), message_id)
) WITH CLUSTERING ORDER BY (message_id DESC);
```""",
        "workflow": """### Life of a Chat Message:
1. User A types a message and sends it over their existing WebSocket connection.
2. WebSocket Server 1 receives packet, validates authentication token, and queries Redis Session Registry for User B's active WebSocket server ID.
3. If User B is **Online**:
   - WebSocket Server 1 publishes message to Kafka partition routed to WebSocket Server 2.
   - WebSocket Server 2 pushes message immediately down User B's open socket.
   - User B's app sends `Delivered` ACK back $\\rightarrow$ routed to User A to update UI to double checkmarks.
4. If User B is **Offline**:
   - Message is stored in Cassandra with `status='SENT'`.
   - Push Notification Service dispatches APNs/FCM push to User B's phone.
   - When User B reconnects, their client queries `GET /conversations/{id}/sync?since={last_message_id}` to download pending messages.""",
        "deep_dive": """### Deep Dive & Technical Challenges:
1. **Handling 50M Open WebSocket Connections:**
   - Linux epoll servers (Go / Netty / Rust) handle 50,000–100,000 idle TCP connections per server.
   - 50M connections $\\rightarrow$ fleet of ~500–1,000 WebSocket gateways managed behind Layer 4 TCP Load Balancers.
2. **Group Chat Fan-out:**
   - For small/medium groups (< 1,000 users): WebSocket server fetches group membership list from Redis and fans out messages to all active member sockets.
   - For massive channels (> 100k users): Use pub/sub topic partitioning and client-side pull models to avoid server memory exhaustion.
3. **End-to-End Encryption (Signal Protocol):**
   - Server only relays encrypted ciphertexts and public pre-keys; servers have zero visibility into plaintext content."""
    },

    # -------------------------------------------------------------------------
    # 3. Zomato / Swiggy / DoorDash
    # -------------------------------------------------------------------------
    {
        "title": "Design Zomato / Swiggy / DoorDash (Food Delivery Platform)",
        "product_target": "Zomato / Swiggy / DoorDash / Uber Eats",
        "category": "Real-Time Geospatial & E-Commerce",
        "difficulty": "Hard",
        "role": "Senior Software Engineer / Staff Architect",
        "summary": "Design a high-scale food delivery platform connecting customers, restaurants, and delivery drivers with real-time dispatch, live GPS order tracking, and inventory management.",
        "functional_reqs": [
            "Restaurant & Menu Discovery: Search nearby restaurants by location, cuisine, ratings, and dietary preferences.",
            "Cart & Checkout: Add items, apply promo coupons, and complete payment.",
            "Order State Machine: Real-time status transitions (`PLACED -> RESTAURANT_ACCEPTED -> FOOD_PREPARING -> DRIVER_ASSIGNED -> OUT_FOR_DELIVERY -> DELIVERED`).",
            "Driver Dispatch & Matching: Real-time matching of optimal delivery partner based on proximity, traffic, and restaurant preparation time.",
            "Live Delivery Tracking: Stream live delivery partner GPS location on map with sub-second ETA updates."
        ],
        "non_functional_reqs": [
            "Real-time location tracking updates (< 2 seconds latency).",
            "Zero double-ordering or race conditions during inventory decrement.",
            "High availability (99.99%) especially during lunch/dinner peak meal spikes.",
            "Resilience against sudden network dropouts on driver mobile devices."
        ],
        "estimations": """- **Daily Orders:** 5M orders/day (Peak lunch/dinner: 2,000 orders/second).
- **Active Delivery Partners:** 200,000 active drivers sending GPS coordinates every 4s $\\rightarrow$ **50,000 location updates/sec**.
- **Read Traffic (Menu Browsing):** 50,000 search/menu views/sec.""",
        "architecture_diagram": """```mermaid
flowchart TD
    Customer[Customer App] -->|1. Search / Place Order| LB[Load Balancer]
    LB --> Gateway[API Gateway]
    
    Gateway --> RestaurantService[Restaurant & Menu Service]
    RestaurantService --> ElasticSearch[(ElasticSearch / PostGIS)]
    
    Gateway --> OrderService[Order Management Service]
    OrderService --> OrderDB[(PostgreSQL Primary DB)]
    OrderService -->|2. Order Placed Event| Kafka[Kafka Order Events Topic]
    
    Kafka --> RestaurantGateway[Restaurant Partner Tablet App]
    Kafka --> DispatchEngine[Driver Dispatch & Matching Engine]
    
    Driver[Delivery Driver App] -->|3. GPS ping every 4s (gRPC/UDP)| LocationService[Location Ingestion Gateway]
    LocationService --> RedisGeo[(Redis H3 Geospatial Grid)]
    
    DispatchEngine -->|4. Match Optimal Driver| RedisGeo
    DispatchEngine -->|5. Push Order Offer| Driver
    
    Driver -->|6. Stream GPS| TrackingService[Live Order Tracking Service]
    TrackingService -->|WebSocket Live Map Stream| Customer
```""",
        "data_model": """### Relational Database Schema (PostgreSQL with PostGIS)

```sql
-- Orders Table
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    restaurant_id UUID NOT NULL,
    driver_id UUID NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(30) NOT NULL, -- PLACED, ACCEPTED, PREPARING, PICKED_UP, DELIVERED, CANCELLED
    delivery_lat DECIMAL(9, 6),
    delivery_lon DECIMAL(9, 6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_orders_customer ON orders(customer_id, created_at DESC);

-- Driver Live Telemetry Cache in Redis (Geospatial H3 index):
-- Key: driver:location:{driver_id} -> {lat, lon, status, last_ping}
```""",
        "workflow": """### Step-by-Step Life of a Food Order:
1. **Search & Menu:** Customer searches for 'Biryani'. ElasticSearch filters open restaurants within 7 km using PostGIS geospatial queries.
2. **Order Placement:** Customer checks out. Order Service creates order record with status `PLACED` and publishes event to Kafka `order_created`.
3. **Restaurant Acceptance:** Restaurant merchant tablet receives WebSocket notification and clicks `Accept` (Estimated Prep Time: 20 mins). Status transitions to `PREPARING`.
4. **Intelligent Driver Dispatch:**
   - 10 minutes before food is ready, Dispatch Engine calculates when a driver should arrive to minimize driver waiting time.
   - Queries Redis Geospatial index (Uber H3 / Geohash) to find top 5 idle drivers within 3 km.
   - Sends order offer to closest driver with 30-second accept countdown.
5. **Live Tracking:** Driver accepts order, arrives at restaurant, picks up package (`PICKED_UP`), and drives to customer. Driver GPS pings Redis every 4 seconds, streamed via WebSockets to Customer map screen.""",
        "deep_dive": """### Deep Dive & Core Engineering Challenges:
1. **Dispatch Optimization & Batching (Order Pooling):**
   - If two customers living in the same apartment complex order from neighboring restaurants within 5 minutes, the Dispatch Engine batches both deliveries to a single driver, cutting delivery costs by 40%.
2. **Preventing Driver Double-Assignment:**
   - When offering an order to a driver, acquire an atomic Redis lock (`SET driver:lock:id token NX EX 30`).
   - Transitioning order state uses optimistic database locking (`UPDATE orders SET driver_id = :id WHERE id = :order_id AND driver_id IS NULL`).
3. **Handling Peak Lunch/Dinner Spikes:**
   - Menu viewing is 95% read-heavy: cached aggressively in Redis / Cloudflare Edge CDN.
   - Order placement enters Kafka queue for buffered asynchronous ingestion to protect primary transactional databases."""
    },

    # -------------------------------------------------------------------------
    # 4. Uber / Lyft / Ola
    # -------------------------------------------------------------------------
    {
        "title": "Design Uber / Lyft (Ride-Hailing & Real-Time Dispatch)",
        "product_target": "Uber / Lyft / Ola / Grab",
        "category": "Real-Time Geospatial & Dispatch Systems",
        "difficulty": "Hard",
        "role": "Staff Software Engineer / Principal Architect",
        "summary": "Design a real-time ride-hailing and dispatch system matching riders with nearby drivers in sub-seconds with dynamic surge pricing and live trip tracking.",
        "functional_reqs": [
            "Drivers stream live GPS locations every 4 seconds.",
            "Riders request rides specifying pickup and dropoff coordinates.",
            "Match riders with the optimal nearby driver in sub-seconds.",
            "Live trip tracking, dynamic route navigation, and real-time ETA calculation.",
            "Dynamic surge pricing based on local supply/demand density."
        ],
        "non_functional_reqs": [
            "Ultra-low latency driver matchmaking (< 1 second).",
            "Real-time driver location updates (< 1s staleness).",
            "Zero double-dispatch race conditions (no two riders assigned to the same driver).",
            "High availability across global metropolitan areas."
        ],
        "estimations": """- **Active Drivers:** 2M active drivers sending GPS every 4s $\\rightarrow$ **500,000 location updates/sec**.
- **Ride Requests:** 50,000 ride requests/sec peak.
- **Geospatial Memory:** 2M drivers * 100 bytes state in Redis = **~200 MB RAM** (extremely compact; partitioned by city).""",
        "architecture_diagram": """```mermaid
flowchart TD
    Driver[Driver Mobile App] -->|GPS updates every 4s (gRPC / UDP)| IngestGateway[Location Ingestion Gateway]
    IngestGateway --> RedisH3[(Redis Geospatial H3 / Ring Buffer)]
    
    Rider[Rider Mobile App] -->|1. Request Ride| DispatchService[Dispatch & Matching Engine]
    
    DispatchService -->|2. Query Nearby Drivers in H3 Cell| RedisH3
    DispatchService -->|3. Calculate ETA & Route| RoutingEngine[Routing & ETA Engine (OSRM / GraphHopper)]
    DispatchService -->|4. Compute Surge Multiplier| SurgePricing[Surge Pricing Service]
    
    DispatchService -->|5. Atomic Driver Reservation via Redlock| Lock[(Distributed Lock)]
    DispatchService -->|6. Offer Ride| Driver
    
    Driver -->|7. Accept Ride| TripService[Trip Management Service]
    TripService --> TripDB[(PostgreSQL Trip DB)]
    TripService -->|Live Trip WebSocket Stream| Rider
```""",
        "data_model": """### Geospatial Partitioning Model (Uber H3 Indexing)
- Earth surface partitioned into hierarchical hexagonal cells (H3 Resolution 8 $\\approx$ 460m radius).
- **Redis H3 Set:**
  - Key: `h3:cell:8828308281fffff` $\\rightarrow$ Set of active `driver_ids`.

```sql
CREATE TABLE trips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rider_id UUID NOT NULL,
    driver_id UUID NULL,
    status VARCHAR(20) NOT NULL, -- REQUESTED, MATCHED, ARRIVED, IN_PROGRESS, COMPLETED
    pickup_lat DECIMAL(9, 6),
    pickup_lon DECIMAL(9, 6),
    dropoff_lat DECIMAL(9, 6),
    dropoff_lon DECIMAL(9, 6),
    surge_multiplier DECIMAL(3, 2) DEFAULT 1.0,
    fare_amount DECIMAL(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```""",
        "workflow": """### Life of an Uber Ride Request:
1. Rider opens app: app pings Dispatch Service with pickup coordinates.
2. System queries Redis H3 cell and neighboring 6 cells (`kRing(1)`) to display 8 nearby car icons on rider's map.
3. Rider clicks 'Request UberX':
   - Surge Pricing Service computes supply (available drivers in H3 cell) vs demand (active riders) $\\rightarrow$ sets multiplier (e.g. 1.4x).
   - Dispatch Engine sorts candidate drivers by ETA using OSRM routing.
   - Acquires Redis distributed lock on closest driver and sends ride dispatch push notification.
4. Driver accepts within 15 seconds $\\rightarrow$ Trip state changes to `MATCHED` $\\rightarrow$ Driver route to pickup streams live to rider via WebSocket.""",
        "deep_dive": """### Deep Dive & Critical Engineering Highlights:
1. **Why Hexagons (H3) vs Squares (Geohash):**
   - In a square grid, diagonal neighbors are $\\sqrt{2}$ times farther than orthogonal neighbors.
   - In a hexagonal grid (H3), all 6 neighboring cells are equidistant, simplifying radius expansions and smoothing search algorithms.
2. **Handling Driver Rejection / Timeout:**
   - If driver rejects or timer expires (15s), release Redis lock, mark driver as temporarily skipped for this trip, and immediately cascade offer to the 2nd best driver in the candidate queue."""
    },

    # -------------------------------------------------------------------------
    # 5. Instagram / TikTok
    # -------------------------------------------------------------------------
    {
        "title": "Design Instagram / TikTok (Photo & Video Social Platform)",
        "product_target": "Instagram / TikTok / Pinterest",
        "category": "High-Scale Media & Content Sharing",
        "difficulty": "Hard",
        "role": "Senior Software Engineer / Staff SWE",
        "summary": "Design a high-scale multimedia sharing platform supporting image/video feed generation, 24-hour stories, user follow graphs, and real-time like/comment interactions.",
        "functional_reqs": [
            "Upload photos and short-form videos with captions and tags.",
            "Personalized chronological / algorithmic Home Feed.",
            "24-Hour Stories that automatically expire after 1 day.",
            "Follow/unfollow users, like posts, and post comments."
        ],
        "non_functional_reqs": [
            "Feed rendering latency < 200ms.",
            "High availability with eventual consistency.",
            "Scalable media storage with global CDN edge caching."
        ],
        "estimations": """- **DAU:** 500M Daily Active Users.
- **Uploads:** 100M media posts/day $\\rightarrow$ **~1,200 write QPS**.
- **Feed Views:** 500M * 20 feed views = 10B views/day $\\rightarrow$ **~120,000 read QPS** (Read-to-Write ratio: 100:1).
- **Storage:** 100M posts * 2 MB average media = **200 TB/day $\\rightarrow$ ~73 PB/year S3 storage**.""",
        "architecture_diagram": """```mermaid
flowchart TD
    Creator[Content Creator] -->|1. Direct Multipart Upload| S3Raw[(S3 Media Storage Bucket)]
    S3Raw -->|2. S3 Notification| Kafka[Media Processing Queue]
    
    Kafka --> TranscodeWorkers[Media Transcoder & Image Optimizer]
    TranscodeWorkers -->|3. WebP / HLS Multi-Res Chunks| S3Processed[(S3 Processed Media Bucket)]
    
    Viewer[Viewer / Follower] -->|4. View Feed| Gateway[API Gateway]
    Gateway --> FeedService[Feed Generation Service]
    
    FeedService -->|5. Fetch Pre-computed Feed| RedisFeed[(Redis Feed Sorted Sets)]
    FeedService -->|6. Cache Miss / Celebrity Merge| PostDB[(Cassandra / PostgreSQL Post DB)]
    
    Viewer -->|7. Load Images / Video| CDN[Cloudflare / CloudFront Edge CDN]
    CDN -->|Cache Hit 95%| Viewer
```""",
        "data_model": """```sql
CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    media_url TEXT NOT NULL,
    thumbnail_url TEXT NOT NULL,
    caption TEXT,
    likes_count BIGINT DEFAULT 0,
    comments_count BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_posts_user ON posts(user_id, created_at DESC);

-- Stories Table with TTL
CREATE TABLE stories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    media_url TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```""",
        "workflow": """### Life of an Instagram Post:
1. User uploads photo: client uploads binary directly to S3 via pre-signed URL.
2. Lambda/Worker resizes image to multiple resolutions (thumbnail, 1080p WebP).
3. Metadata saved in PostgreSQL/Cassandra.
4. Fan-out Worker pushes post ID into all followers' Redis timeline Sorted Sets (`ZADD user_feed:{follower_id} <timestamp> <post_id>`).""",
        "deep_dive": """### Deep Dive & Optimizations:
1. **The Celebrity Fan-out Dilemma:**
   - Accounts with 50M+ followers (e.g. Cristiano Ronaldo) cannot fan-out on write (pushing to 50M Redis lists causes huge lag).
   - **Solution:** Hybrid Fanout: Regular users use Fan-out on Write (Push). Celebrities use Fan-out on Read (Pull). When a user opens their feed, the server fetches their push feed from Redis and merges it with the latest posts of celebrities they follow."""
    },

    # -------------------------------------------------------------------------
    # 6. BookMyShow / Ticketmaster
    # -------------------------------------------------------------------------
    {
        "title": "Design BookMyShow / Ticketmaster (Concert & Movie Ticket Booking)",
        "product_target": "BookMyShow / Ticketmaster / Eventbrite",
        "category": "High-Concurrency Transactional Systems",
        "difficulty": "Hard",
        "role": "Staff Software Engineer / Transactional Systems Architect",
        "summary": "Design a high-concurrency seat reservation and ticketing engine preventing double-booking during viral concert ticket sales.",
        "functional_reqs": [
            "Browse movies/concerts, venues, showtimes, and interactive seat maps.",
            "Temporarily lock/reserve chosen seats for 10 minutes during payment.",
            "Confirm booking upon payment or release locked seats automatically if checkout expires.",
            "Prevent any seat from being double-booked."
        ],
        "non_functional_reqs": [
            "Strict zero double-booking (seat allocation is 100% mutually exclusive).",
            "High concurrency handling (500,000 users competing for 20,000 stadium seats).",
            "Idempotent payment capture and atomic inventory release on timeout."
        ],
        "estimations": """- **Concert Sale Spike:** 500,000 users hitting 'Reserve Seats' within 10 seconds of tickets opening $\\rightarrow$ **50,000 QPS burst**.""",
        "architecture_diagram": """```mermaid
flowchart TD
    User[500,000 Fans] -->|1. Book Seats 12A, 12B| LB[Load Balancer]
    LB --> Gateway[Virtual Waiting Room / Queue-it API Gateway]
    
    Gateway --> BookingService[Seat Reservation Service]
    BookingService -->|2. Atomic Seat Lock Lua Script| RedisSeats[(Redis Seat Lock State - TTL 10m)]
    
    RedisSeats -->|Lock Acquired: Token Issued| BookingService
    RedisSeats -.->|Seat Already Locked / Sold| Reject[Seat Unavailable - Choose Another]
    
    BookingService -->|3. Publish Lock Event| DelayQueue[RabbitMQ / Redis Delayed Exchange (10m TTL)]
    
    BookingService --> PaymentService[Payment Gateway]
    PaymentService -->|4. Payment Success| OrderService[Order Fulfillment Service]
    OrderService --> DB[(PostgreSQL Primary Booking DB)]
    
    DelayQueue -.->|If No Payment in 10m| AutoReleaseWorker[Auto-Release Expired Seats Worker]
    AutoReleaseWorker --> RedisSeats
```""",
        "data_model": """```sql
CREATE TABLE show_seats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    show_id UUID NOT NULL,
    seat_number VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL, -- AVAILABLE, LOCKED, BOOKED
    locked_by_user UUID NULL,
    lock_expires_at TIMESTAMP WITH TIME ZONE NULL,
    version INT NOT NULL DEFAULT 0,
    UNIQUE(show_id, seat_number)
);
```""",
        "workflow": """### Life of a Ticket Reservation:
1. User selects Seat 14B and clicks 'Proceed to Pay'.
2. Booking service executes atomic Lua script on Redis:
   - Checks if key `seat:show_123:14B` exists.
   - If not, sets key with value `user_999` and TTL of 600 seconds (10 mins).
3. Simultaneously updates PostgreSQL database using optimistic concurrency control:
   ```sql
   UPDATE show_seats 
   SET status = 'LOCKED', locked_by_user = 'user_999', lock_expires_at = NOW() + INTERVAL '10 minutes', version = version + 1
   WHERE show_id = 'show_123' AND seat_number = '14B' AND status = 'AVAILABLE';
   ```
4. If payment succeeds in 3 minutes $\\rightarrow$ status changes to `BOOKED`.
5. If user abandons payment $\\rightarrow$ Redis TTL expires and delayed worker resets status to `AVAILABLE`.""",
        "deep_dive": """### Deep Dive & Engineering Concurrency:
1. **Preventing Race Conditions (Optimistic vs Pessimistic vs Redis):**
   - Direct database pessimistic locking (`SELECT ... FOR UPDATE`) causes database connection pool exhaustion under 50k QPS.
   - **Solution:** Multi-tier locking: Redis atomic operations filter out 99.9% of redundant competing requests in memory, allowing only winning requests to hit the relational database."""
    }
]

def main():
    logger.info(f"Generating full standard HLD blueprints ({len(STANDARD_HLD_QUESTIONS)} core systems)...")

    # Combine with existing canonical list
    canonical_file = os.path.join(os.path.dirname(__file__), "..", "canonical_system_design_questions.json")
    with open(canonical_file, "w", encoding="utf-8") as f:
        json.dump(STANDARD_HLD_QUESTIONS, f, indent=2)

    logger.info(f"✅ Exported standard HLD questions to {canonical_file}")

if __name__ == "__main__":
    main()
