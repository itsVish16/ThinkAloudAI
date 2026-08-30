import json
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SYSTEM_DESIGN_QUESTIONS = [
    # -------------------------------------------------------------------------
    # 1. Foundational Classic Distributed Systems
    # -------------------------------------------------------------------------
    {
        "title": "Design a URL Shortener (TinyURL / Bit.ly)",
        "domain": "Backend / Core Distributed Systems",
        "role": "Software Engineer / Senior Software Engineer",
        "summary": "Design a scalable URL shortener service that generates unique short aliases for long URLs and handles billions of high-speed redirects.",
        "functional_requirements": [
            "Given a long URL, generate a shorter and unique alias (e.g. https://tinyurl.com/aB3x9Z).",
            "When users access a short URL, redirect them immediately to the original long URL with HTTP 301/302.",
            "Users can optionally specify custom aliases and expiration dates.",
            "System collects analytics (click count, geolocations, referrers)."
        ],
        "non_functional_requirements": [
            "Ultra-low latency redirects (< 20ms read latency).",
            "High availability (99.99%) - read traffic must never fail.",
            "Short URL aliases must be non-predictable and collision-resistant."
        ],
        "estimations": {
            "traffic": "100M new URLs created/month, 10B clicks/month (100:1 Read-to-Write ratio).",
            "qps": "Write QPS: ~40 writes/sec (Peak: 100/s). Read QPS: ~4,000 reads/sec (Peak: 10,000/s).",
            "storage": "100M * 12 months * 5 years = 6B records. Each record ~500 bytes -> 3 TB total storage over 5 years.",
            "cache": "Cache 20% hot URLs (Pareto 80/20 rule): 10B * 0.20 * 500 bytes / 30 days = ~33 GB RAM for Redis cache."
        },
        "data_model": """### Database Schema

**`urls` Table (NoSQL Key-Value / MongoDB / DynamoDB or PostgreSQL with Hash Sharding):**
```sql
CREATE TABLE urls (
    short_key VARCHAR(10) PRIMARY KEY,      -- Base62 encoded key (e.g. '7kX9pQ')
    original_url TEXT NOT NULL,
    user_id BIGINT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NULL
);
CREATE INDEX idx_user_created ON urls(user_id, created_at);
```

**`click_events` Table (Time-Series DB / ClickHouse / Cassandra):**
```sql
CREATE TABLE click_events (
    short_key VARCHAR(10),
    clicked_at TIMESTAMP WITH TIME ZONE,
    ip_address VARCHAR(45),
    country VARCHAR(3),
    referer TEXT,
    PRIMARY KEY (short_key, clicked_at)
);
```""",
        "architecture_diagram": """```mermaid
flowchart TD
    Client[User / Browser] -->|GET /7kX9pQ| CDN[Cloudflare CDN / Edge Cache]
    CDN -->|Cache Miss| LB[Load Balancer]
    LB --> API[URL Shortener Service]
    API -->|1. Fast Lookup| Redis[Redis Cache Cluster - LRU]
    API -->|2. Cache Miss| DB[(Distributed DB - DynamoDB / MongoDB)]
    
    Client -->|POST /shorten| LB
    API --> KGS[Key Generation Service / Zookeeper Range Allocator]
    API -->|Async Event| Kafka[Kafka Click Stream]
    Kafka --> AnalyticsWorker[Analytics Aggregator]
    AnalyticsWorker --> AnalyticsDB[(ClickHouse Analytics DB)]
```""",
        "deep_dive": """### Deep Dive & Key Engineering Trade-offs

1. **Short URL Generation Strategies:**
   - **Hashing (MD5 / SHA-256) + Base62:** Hashing the URL yields a 128-bit hash. Taking the first 7 characters in Base62 ($62^7 \approx 3.5$ trillion combinations) causes hash collisions. Collision resolution loops add database latency.
   - **Pre-generated Unique Keys (Key Generation Service - KGS):** A standalone worker pre-generates 7-character Base62 keys in batches, storing them in two tables: `used_keys` and `unused_keys`. When shortener instances start, they load $10,000$ keys into memory. Guarantees zero runtime collisions and $O(1)$ writes.

2. **Redirect Status: HTTP 301 vs 302:**
   - **HTTP 301 (Permanent Redirect):** Browser caches the redirect permanently. Subsequent requests bypass the shortener server, saving backend load but preventing accurate click analytics tracking.
   - **HTTP 302 (Temporary Redirect):** Every click hits the shortener service first, ensuring 100% accurate click analytics and immediate expiration enforcement at the cost of slightly higher server load.

3. **Cache Invalidation & Stampede:**
   - Cache with TTL. If a key expires, use Redis Mutex/Distributed Lock to prevent thousands of simultaneous cache misses from hammering the database."""
    },
    # -------------------------------------------------------------------------
    # 2. Rate Limiter
    # -------------------------------------------------------------------------
    {
        "title": "Design an API Rate Limiter",
        "domain": "Infrastructure / Security / API Gateway",
        "role": "Software Engineer / Senior Software Engineer",
        "summary": "Design a high-throughput, low-latency distributed rate limiter to protect backend APIs from abuse, DDoS attacks, and resource exhaustion.",
        "functional_requirements": [
            "Limit client requests based on IP address, User ID, or API Key (e.g. 100 requests/minute).",
            "Return HTTP 429 (Too Many Requests) with standard headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`).",
            "Support configurable rate tiers per client tier (Free, Pro, Enterprise)."
        ],
        "non_functional_requirements": [
            "Sub-millisecond processing overhead (< 2ms per request).",
            "Accurate distributed tracking across multi-region server clusters.",
            "High availability with graceful fallback (fail-open) if rate limiter nodes fail."
        ],
        "estimations": {
            "traffic": "10M active users, 100,000 API requests/second peak.",
            "storage": "10M users * 64 bytes per user rate state in Redis = ~640 MB of RAM (extremely compact)."
        },
        "data_model": """### In-Memory Storage Model (Redis)

**Token Bucket Redis Hash:**
```redis
HSET ratelimit:user_12345 tokens 45 last_refill 1718901234
EXPIRE ratelimit:user_12345 3600
```

**Sliding Window Log Redis Sorted Set (ZSET):**
```redis
ZADD ratelimit:ip_192.168.1.1 1718901234.500 "req_uuid_1"
ZREMRANGEBYSCORE ratelimit:ip_192.168.1.1 -inf (current_time - 60)
ZCARD ratelimit:ip_192.168.1.1
```""",
        "architecture_diagram": """```mermaid
flowchart TD
    Client[Client App] -->|HTTP Request| LB[Load Balancer]
    LB --> Gateway[API Gateway / Envoy Reverse Proxy]
    Gateway -->|1. Check Rate Limit Lua Script| RedisCluster[Redis Cluster - Primary/Replica]
    RedisCluster -->|2. Allowed (Remaining: 84)| Gateway
    Gateway -->|3. Forward Request| Microservices[Backend Microservices]
    
    Gateway -.->|Over Limit| 429Resp[HTTP 429 Too Many Requests]
```""",
        "deep_dive": """### Deep Dive & Comparison of Algorithms

| Algorithm | Pros | Cons | Best Used For |
|---|---|---|---|
| **Token Bucket** | Handles bursts gracefully; memory efficient ($O(1)$ space). | Reset boundary tuning needed. | General API rate limiting (AWS, Stripe). |
| **Leaky Bucket** | Guarantees perfectly smooth, constant egress rate. | Bursts can drop legitimate traffic if queue fills. | E-commerce checkouts, message egress. |
| **Sliding Window Log** | 100% accurate; no boundary burst anomalies. | High memory ($O(N)$ requests in window stored in ZSET). | Strict credit card transaction limits. |
| **Sliding Window Counter** | Blends memory efficiency with accurate rolling window. | Approximation (~0.05% error rate). | High-scale global API gateways. |

#### Concurrency & Race Conditions:
- When multiple concurrent requests from the same user hit different gateway instances simultaneously, read-modify-write causes race conditions.
- **Solution:** Execute rate-limiting logic atomically inside Redis using **Lua Scripts** or Redis `evalsha`. Redis single-threaded execution guarantees atomic token decrement without distributed locks."""
    },
    # -------------------------------------------------------------------------
    # 3. Distributed Key-Value Store / Cache
    # -------------------------------------------------------------------------
    {
        "title": "Design a Distributed Key-Value Store (DynamoDB / Cassandra)",
        "domain": "Distributed Storage / Core Backend",
        "role": "Senior Software Engineer / Staff Engineer",
        "summary": "Design a highly scalable, fault-tolerant, horizontally partitioned distributed key-value store with tunable consistency.",
        "functional_requirements": [
            "Support `put(key, value)` and `get(key)` operations.",
            "Support values up to 1 MB.",
            "Configurable consistency levels (Strong vs Eventual)."
        ],
        "non_functional_requirements": [
            "Massive horizontal scalability (petabytes of data, millions of QPS).",
            "High availability with automatic partition recovery.",
            "Sub-10ms read/write latency at P99."
        ],
        "estimations": {
            "traffic": "100,000 write QPS, 1,000,000 read QPS.",
            "storage": "10B keys * 1 KB average size = 10 TB active dataset, replicated 3x = 30 TB."
        },
        "data_model": """### Node Storage Engine (LSM-Tree / RocksDB)
- **MemTable (In-Memory SkipList / Red-Black Tree):** Buffers incoming writes sorted by key.
- **Write-Ahead Log (WAL):** Appends raw writes to disk for crash recovery.
- **SSTables (Sorted String Tables on Disk):** Immutable files created when MemTable flushes.
- **Bloom Filters:** Fast probabilistic bitmap in RAM checking if a key exists in an SSTable before disk I/O.""",
        "architecture_diagram": """```mermaid
flowchart TD
    Client -->|get/put| Coord[Coordinator Node]
    
    subgraph Consistent Hash Ring
        NodeA[Node A (Virtual Nodes)]
        NodeB[Node B (Virtual Nodes)]
        NodeC[Node C (Virtual Nodes)]
        NodeD[Node D (Virtual Nodes)]
    end
    
    Coord -->|Replicate N=3| NodeA
    Coord -->|Replicate N=3| NodeB
    Coord -->|Replicate N=3| NodeC
    
    subgraph Storage Engine Inside Each Node
        WAL[Write-Ahead Log]
        MemTable[In-Memory MemTable]
        Bloom[Bloom Filter]
        SSTable[(Disk SSTables Level 0..N)]
    end
```""",
        "deep_dive": """### Deep Dive & Key Engineering Trade-offs

1. **Consistent Hashing with Virtual Nodes:**
   - Hash keys and nodes onto a $2^{32} - 1$ ring using MurmurHash3.
   - Assign 256 virtual nodes per physical machine to ensure uniform data distribution and eliminate hot partitions.

2. **Tunable Quorum Consistency ($N, W, R$):**
   - $N$: Replication factor (typically 3).
   - $W$: Write quorum size (number of positive write acks needed).
   - $R$: Read quorum size (number of replica responses needed).
   - **Strong Consistency:** $W + R > N$ (e.g. $N=3, W=2, R=2$).
   - **High-Speed Eventual Consistency:** $W=1, R=1$ for maximum availability.

3. **Conflict Resolution & Vector Clocks:**
   - In eventual consistency, network partitions cause concurrent divergent writes.
   - Use **Vector Clocks** to detect causality violations and **Last-Write-Wins (LWW)** with NTP-synchronized TrueTime or client-side conflict resolution."""
    },
    # -------------------------------------------------------------------------
    # 4. Distributed Message Queue
    # -------------------------------------------------------------------------
    {
        "title": "Design a Distributed Message Queue (Apache Kafka / RabbitMQ)",
        "domain": "Distributed Systems / Event Streaming",
        "role": "Senior Software Engineer / Staff Engineer",
        "summary": "Design a high-throughput, fault-tolerant distributed pub/sub event streaming platform capable of handling millions of events/sec with ordered partitions.",
        "functional_requirements": [
            "Publish messages to topics (`publish(topic, message)`).",
            "Subscribe and consume messages by consumer groups (`consume(topic, group_id)`).",
            "Message persistence, replayability from arbitrary offsets, and TTL retention."
        ],
        "non_functional_requirements": [
            "Extreme throughput (1M+ events/sec).",
            "Strict message ordering within individual partitions.",
            "At-least-once or exactly-once delivery guarantees."
        ],
        "estimations": {
            "traffic": "1M messages/sec write, 5M messages/sec read (multiple consumer fan-out).",
            "bandwidth": "1M msg/s * 1 KB = 1 GB/s ingress, 5 GB/s egress.",
            "storage": "1 GB/s * 86,400s * 7 days retention = ~600 TB disk storage."
        },
        "data_model": """### Disk Storage Format (Append-Only Commit Log)
- Topic is divided into **Partitions**.
- Each partition is stored on disk as ordered segment files (`00000000.log`, `00000000.index`).
- Messages are written sequentially using OS page cache and `sendfile` zero-copy system call.""",
        "architecture_diagram": """```mermaid
flowchart TD
    Producers[Producers Cluster] -->|Publish messages| BrokerLeader[Broker 1 - Partition Leader]
    
    subgraph Kafka Broker Cluster
        BrokerLeader -->|Sync Replication| BrokerFollower1[Broker 2 - Follower]
        BrokerLeader -->|Sync Replication| BrokerFollower2[Broker 3 - Follower]
    end
    
    KRaft[KRaft / Zookeeper Cluster Coordinator] -.->|Metadata & Leader Election| BrokerLeader
    
    BrokerLeader -->|Sequential Pull| Consumer1[Consumer Group A - Worker 1]
    BrokerLeader -->|Sequential Pull| Consumer2[Consumer Group A - Worker 2]
    BrokerLeader -->|Independent Pull| ConsumerB[Consumer Group B - Analytics]
```""",
        "deep_dive": """### Deep Dive & Throughput Optimizations

1. **Why Kafka is Incredibly Fast (The 4 Pillars):**
   - **Sequential Disk I/O:** Sequential writes to disk are nearly as fast as RAM (~600 MB/s on NVMe), avoiding random seeks.
   - **Zero-Copy Data Transfer (`sendfile`):** Transfers data directly from OS Page Cache to Network Socket without copying into user-space JVM memory.
   - **Batching & Compression:** Batches messages at producer and broker level with Snappy/Zstandard compression.
   - **Pull vs Push Consumer Model:** Consumers pull at their own processing rate, preventing fast producers from overwhelming slow consumers."""
    },
    # -------------------------------------------------------------------------
    # 5. Video Streaming Platform
    # -------------------------------------------------------------------------
    {
        "title": "Design a Video Streaming Platform (YouTube / Netflix)",
        "domain": "Full-Stack / Media & Cloud Architecture",
        "role": "Senior Software Engineer / Staff Infrastructure Engineer",
        "summary": "Design a global video ingestion, transcoding, and adaptive bitrate streaming platform supporting millions of concurrent viewers.",
        "functional_requirements": [
            "Upload videos of arbitrary formats and resolutions up to 4K.",
            "Stream videos smoothly with adaptive bitrate (HLS / DASH).",
            "Search, view video metadata, like, comment, and view counts.",
            "View count accurately tracked at massive scale."
        ],
        "non_functional_requirements": [
            "High streaming availability with minimal buffering and fast startup time.",
            "Global low-latency delivery via CDN edge nodes.",
            "Scalable asynchronous transcoding worker fleet."
        ],
        "estimations": {
            "traffic": "500 hours of video uploaded/minute. 1B daily active viewers.",
            "storage": "500 hrs/min * 60 min * 24 hrs * 3 GB/hr encoded = ~2 PB new video storage per day."
        },
        "data_model": """### Database Schema

**`videos` Table (PostgreSQL):**
```sql
CREATE TABLE videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uploader_id BIGINT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    duration_seconds INT NOT NULL,
    manifest_url TEXT NOT NULL,           -- HLS master playlist URL (.m3u8)
    thumbnail_url TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'PROCESSING', -- PENDING, PROCESSING, READY, FAILED
    views_count BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```""",
        "architecture_diagram": """```mermaid
flowchart TD
    Creator[Content Creator] -->|1. Upload Raw MP4| S3Raw[(S3 Raw Video Bucket)]
    S3Raw -->|2. S3 Event Notification| Kafka[Transcode Task Queue]
    
    Kafka --> TranscodeWorkers[Distributed Transcoding Fleet (FFmpeg / GPU)]
    TranscodeWorkers -->|3. Multi-bitrate Chunks 1080p, 720p, 480p| S3Processed[(S3 Processed Video Chunks)]
    
    Viewer[Viewer Device] -->|4. Request Video Stream| EdgeCDN[Global CDN Edge (Cloudflare/Fastly)]
    EdgeCDN -->|Cache Hit (98%)| Viewer
    EdgeCDN -->|Cache Miss| S3Processed
    
    Viewer -->|Increment View Counter| ViewAggregator[Redis HyperLogLog & Aggregator]
    ViewAggregator --> DB[(PostgreSQL Video DB)]
```""",
        "deep_dive": """### Deep Dive & Video Processing Mechanics

1. **Adaptive Bitrate Streaming (HLS & DASH):**
   - Transcoder splits the video into 2 to 6-second `.ts` or `.m4s` chunks across multiple resolutions (1080p, 720p, 480p, 360p).
   - Generates an `index.m3u8` master playlist. The player dynamically switches resolutions based on client network bandwidth.

2. **Deduplication & View Counter Accuracy:**
   - Use **HyperLogLog** in Redis to count unique views per video per user per 24 hours to prevent view count manipulation."""
    },
    # -------------------------------------------------------------------------
    # 6. Real-Time Chat System
    # -------------------------------------------------------------------------
    {
        "title": "Design a Real-Time Chat Application (WhatsApp / Discord / Slack)",
        "domain": "Real-Time Systems / WebSockets / Distributed Messaging",
        "role": "Senior Software Engineer",
        "summary": "Design a real-time 1-on-1 and group chat system supporting online presence, message delivery receipts, offline storage, and end-to-end encryption.",
        "functional_requirements": [
            "1-on-1 direct messaging and multi-user group chat (up to 500 members).",
            "Message delivery status (Sent, Delivered, Read).",
            "Online / offline presence tracking and typing indicators.",
            "Media attachments (photos, videos, files)."
        ],
        "non_functional_requirements": [
            "Real-time low latency delivery (< 100ms P99).",
            "Guaranteed message ordering per conversation.",
            "Durability: no message loss even during network disconnections."
        ],
        "estimations": {
            "traffic": "500M DAU, 50B messages/day -> ~600,000 messages/sec peak.",
            "connections": "50M concurrent open WebSocket connections.",
            "storage": "50B messages * 200 bytes = 10 TB/day -> 3.6 PB/year."
        },
        "data_model": """### Database Schema (ScyllaDB / Cassandra)

```sql
CREATE TABLE messages (
    conversation_id UUID,
    message_id TIMEUUID,                  -- Provides deterministic temporal ordering
    sender_id UUID,
    content TEXT,
    media_url TEXT,
    created_at TIMESTAMP,
    PRIMARY KEY ((conversation_id), message_id)
) WITH CLUSTERING ORDER BY (message_id DESC);
```""",
        "architecture_diagram": """```mermaid
flowchart TD
    UserA[User A Mobile] <-->|Persistent WebSocket| WS1[Chat WebSocket Server 1]
    UserB[User B Mobile] <-->|Persistent WebSocket| WS2[Chat WebSocket Server 2]
    
    WS1 -->|Lookup User Connection| RedisRegistry[(Redis Session Registry)]
    WS1 -->|Publish Message| Kafka[Kafka / Pulsar Message Bus]
    
    Kafka --> MsgPersistenceWorker[Message Persistence Worker]
    MsgPersistenceWorker --> Cassandra[(Cassandra Message Store)]
    
    Kafka --> PushService[Push Notification Service - APNs/FCM]
    PushService -.->|If User Offline| UserB
    
    Kafka --> WS2
    WS2 -->|Forward Real-Time Frame| UserB
```""",
        "deep_dive": """### Deep Dive & Real-Time Engineering

1. **Protocol Choice: WebSockets vs Long Polling vs gRPC:**
   - WebSockets provide persistent full-duplex TCP connections with minimal 2-byte framing overhead, perfect for bi-directional messaging.

2. **Managing 50M Concurrent Connections:**
   - A single high-performance Linux server (e.g. Netty / Go / epoll) handles ~50,000 to 100,000 idle WebSocket connections.
   - 50M connections require ~500–1,000 chat servers distributed behind Layer 4 TCP Load Balancers.
   - Redis cluster maps `user_id -> server_id` to route messages to the exact WebSocket node holding the recipient's socket."""
    },
    # -------------------------------------------------------------------------
    # 7. Proximity / Geolocation Service
    # -------------------------------------------------------------------------
    {
        "title": "Design a Proximity / Nearby Places Service (Yelp / Google Maps)",
        "domain": "Geospatial Systems / Spatial Indexing",
        "role": "Senior Software Engineer",
        "summary": "Design a location-based search service that finds nearby businesses (e.g. restaurants within 5 km) with sub-50ms query latency.",
        "functional_requirements": [
            "Search for businesses by geographic location (latitude, longitude, radius).",
            "Filter by rating, category, and price level.",
            "Business owners can add, update, or remove business profiles."
        ],
        "non_functional_requirements": [
            "Ultra-low search latency (< 50ms).",
            "High read throughput with global geospatial distribution.",
            "High spatial indexing efficiency."
        ],
        "estimations": {
            "traffic": "500M places, 100,000 search queries/sec peak.",
            "storage": "500M places * 1 KB metadata = 500 GB (fits easily in RAM cache)."
        },
        "data_model": """### Spatial Indexing Approaches

1. **Geohash (Base32 String):**
   - Interleaves latitude and longitude bits into hierarchical string prefixes (e.g. `9q8yy`).
   - Shared prefix indicates geographical proximity.

2. **Google S2 / Uber H3 (Hexagonal Hierarchical Index):**
   - Maps Earth surface onto hierarchical regular hexagons. All neighboring cells are equidistant."""
    },
    # -------------------------------------------------------------------------
    # 8. Ride-Sharing Dispatch System
    # -------------------------------------------------------------------------
    {
        "title": "Design a Ride-Sharing Dispatch Platform (Uber / Lyft)",
        "domain": "Real-Time Geospatial / Dispatch & Matching",
        "role": "Staff Software Engineer / Principal Architect",
        "summary": "Design a real-time ride-matching and live location tracking system matching riders with nearby drivers in sub-seconds.",
        "functional_requirements": [
            "Drivers stream live GPS location every 3-5 seconds.",
            "Riders request a ride and get matched with the optimal nearby driver.",
            "Live trip tracking with real-time ETA and route visualization."
        ],
        "non_functional_requirements": [
            "Real-time driver location updates (< 1s staleness).",
            "Zero double-dispatch race conditions (no two riders assigned to same driver).",
            "Resilient against sudden surge traffic and network drops."
        ],
        "estimations": {
            "traffic": "2M active drivers sending GPS every 4s = 500,000 location updates/sec.",
            "storage": "In-memory geospatial grid cache in Redis / In-memory QuadTree cluster."
        },
        "data_model": """### Real-Time Dispatch Pipeline
- **Driver Location Buffer:** Redis Geospatial / In-memory H3 Index updated via UDP/WebSocket.
- **Trip State Machine:** `REQUESTED -> MATCHING -> ACCEPTED -> ARRIVED -> IN_PROGRESS -> COMPLETED`."""
    },
    # -------------------------------------------------------------------------
    # 9. Real-Time Collaborative Document Editor
    # -------------------------------------------------------------------------
    {
        "title": "Design a Collaborative Document Editor (Google Docs / Figma)",
        "domain": "Distributed Algorithms / Real-Time Collaboration",
        "role": "Staff Software Engineer",
        "summary": "Design a multi-user real-time collaborative document editing system supporting concurrent text edits with sub-100ms latency.",
        "functional_requirements": [
            "Multiple users can edit the same document simultaneously.",
            "Real-time cursor positions and selection highlights.",
            "Document revision history, undo/redo, and offline editing sync."
        ],
        "non_functional_requirements": [
            "Convergence: All users must eventually see the exact same document state.",
            "Sub-50ms local typing response without server round-trip blocking.",
            "Conflict resolution without data corruption or lost keystrokes."
        ],
        "estimations": {
            "traffic": "50M active documents, 100M concurrent edit operations/sec peak."
        },
        "data_model": """### Conflict Resolution: OT vs CRDT

| Feature | Operational Transformation (OT) | Conflict-free Replicated Data Types (CRDT) |
|---|---|---|
| **Architecture** | Centralized server acts as source of truth. | Peer-to-peer / decentralized friendly. |
| **Algorithm** | Transforms operations based on server revision state. | Mathematically commutative & idempotent state merges (e.g. Yjs, Automerge). |
| **Complexity** | High server transformation complexity ($O(N^2)$). | Higher memory overhead per character metadata. |
| **Industry Usage** | Google Docs, Microsoft Office Online. | Figma, Apple Notes, Notion, Live Share. |"""
    },
    # -------------------------------------------------------------------------
    # 10. Web Crawler
    # -------------------------------------------------------------------------
    {
        "title": "Design a Scalable Distributed Web Crawler",
        "domain": "Data Engineering / Distributed Crawling",
        "role": "Senior Software Engineer",
        "summary": "Design a distributed web crawler capable of downloading and indexing billions of web pages while respecting politeness and avoiding crawl traps.",
        "functional_requirements": [
            "Download 1 billion web pages per month.",
            "Extract text, metadata, and outgoing links.",
            "Respect robots.txt and host crawl politeness intervals."
        ],
        "non_functional_requirements": [
            "High scalability across hundreds of worker nodes.",
            "Robustness against infinite URL loops and spider traps.",
            "Content deduplication using SimHash / MinHash."
        ],
        "estimations": {
            "throughput": "1B pages / 30 days = ~400 pages/second.",
            "storage": "1B pages * 500 KB average size = 500 TB raw HTML storage/month."
        }
    },
    # -------------------------------------------------------------------------
    # 11. Search Autocomplete / Typeahead System
    # -------------------------------------------------------------------------
    {
        "title": "Design a Search Autocomplete / Typeahead System (Google Search)",
        "domain": "Search Infrastructure / In-Memory Data Structures",
        "role": "Senior Software Engineer",
        "summary": "Design a real-time search autocomplete system that suggests the top 5 most relevant queries within 10ms as users type.",
        "functional_requirements": [
            "Return top 5 suggestions matching user query prefix in real time.",
            "Rank suggestions by historical search frequency and recency."
        ],
        "non_functional_requirements": [
            "Ultra-low latency (< 10ms P99 search response).",
            "High availability and fault tolerance across global edge nodes."
        ],
        "estimations": {
            "traffic": "5B searches/day * 4 keystrokes average = 20B autocomplete requests/day -> ~250,000 QPS peak."
        }
    },
    # -------------------------------------------------------------------------
    # 12. E-Commerce Flash Sale / Checkout System
    # -------------------------------------------------------------------------
    {
        "title": "Design an E-Commerce Flash Sale System (Amazon / Ticketmaster)",
        "domain": "Transactional Systems / Concurrency Control",
        "role": "Staff Software Engineer / Principal Architect",
        "summary": "Design a high-concurrency e-commerce inventory deduction and checkout platform preventing overselling during flash sales.",
        "functional_requirements": [
            "View product inventory and price.",
            "Add to cart and reserve stock during checkout window (10 minutes).",
            "Complete order with payment and decrement final inventory."
        ],
        "non_functional_requirements": [
            "Strict zero overselling (inventory must never drop below 0).",
            "High concurrency handling (100,000 requests/sec competing for 1,000 items).",
            "Idempotent checkout and payment processing."
        ],
        "data_model": """### Concurrency & Inventory Reservation Techniques

1. **Redis Atomic Decrement (`DECRBY` with Lua):**
   - Pre-warm inventory into Redis cache. Execute atomic decrement: if stock >= quantity, decrement and return success.
2. **Pessimistic vs Optimistic DB Locking:**
   - **Pessimistic (`SELECT ... FOR UPDATE`):** Blocks other transactions; causes high DB lock contention.
   - **Optimistic Locking (`WHERE version = :v AND stock >= :qty`):** Fails fast on concurrent modification, ideal for moderate contention.
3. **Database Decrement with Positive Constraint:**
   ```sql
   UPDATE inventory SET available = available - 1 WHERE product_id = 42 AND available > 0;
   ```"""
    },
    # -------------------------------------------------------------------------
    # 13. Payment Gateway & Double-Entry Ledger
    # -------------------------------------------------------------------------
    {
        "title": "Design a Payment Gateway & Double-Entry Ledger System (Stripe)",
        "domain": "Financial Engineering / Distributed Transactions",
        "role": "Staff Software Engineer",
        "summary": "Design a mission-critical payment processing platform guaranteeing exactly-once transaction processing and immutable double-entry accounting.",
        "functional_requirements": [
            "Accept credit card and wallet payments via third-party processors.",
            "Record every monetary movement in an immutable double-entry ledger.",
            "Support refunds, chargebacks, and automated daily reconciliation."
        ],
        "non_functional_requirements": [
            "100% financial correctness and zero double-charging (Strict Idempotency).",
            "Auditability: Immutable append-only transaction log.",
            "High availability with 99.999% uptime."
        ]
    },
    # -------------------------------------------------------------------------
    # 14. Cloud File Storage & Sync
    # -------------------------------------------------------------------------
    {
        "title": "Design a Cloud File Storage & Sync Service (Google Drive / Dropbox)",
        "domain": "Distributed File Systems / Storage Infrastructure",
        "role": "Senior Software Engineer / Staff Engineer",
        "summary": "Design a distributed cloud file storage and cross-device synchronization system supporting delta sync and chunked uploads.",
        "functional_requirements": [
            "Upload, download, edit, and delete files up to 50 GB.",
            "Automatic cross-device file synchronization upon modifications.",
            "File versioning, rollback, and sharing permissions."
        ],
        "non_functional_requirements": [
            "Bandwidth optimization using chunking and delta sync (rsync algorithm).",
            "High data durability (99.999999999% 11 9s).",
            "End-to-end encryption at rest and in transit."
        ]
    },
    # -------------------------------------------------------------------------
    # 15. Distributed Metric Monitoring & Alerting
    # -------------------------------------------------------------------------
    {
        "title": "Design a Metric Monitoring & Alerting Platform (Prometheus / Datadog)",
        "domain": "Observability / Time-Series Systems",
        "role": "Senior Infrastructure Engineer",
        "summary": "Design a distributed metrics collection, time-series storage, and automated alerting engine handling millions of data points per second.",
        "functional_requirements": [
            "Ingest metrics (Counters, Gauges, Histograms) from hundreds of thousands of microservices.",
            "Query metrics using a rich query language (PromQL).",
            "Evaluate alert rules and trigger PagerDuty / Slack notifications."
        ],
        "non_functional_requirements": [
            "High write throughput (10M metric samples/second).",
            "Low query latency for dashboards (< 200ms).",
            "Configurable data retention and automatic downsampling (raw -> 5m -> 1h rollups)."
        ]
    }
]

def main():
    logger.info(f"Exporting {len(SYSTEM_DESIGN_QUESTIONS)} comprehensive System Design blueprints...")
    
    # Save canonical json
    out_json_path = os.path.join(os.path.dirname(__file__), "..", "canonical_system_design_questions.json")
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(SYSTEM_DESIGN_QUESTIONS, f, indent=2)
        
    logger.info(f"✅ Exported to {out_json_path}")

if __name__ == "__main__":
    main()
