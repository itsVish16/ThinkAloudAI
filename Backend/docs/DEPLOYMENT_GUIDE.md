# ThinkAloud.AI — Production Deployment Guide (AWS EC2 & Amazon RDS)

This guide documents the complete deployment of the ThinkAloudAI backend on a single AWS EC2 instance connecting to Amazon RDS PostgreSQL.

---

## 1. Architecture Overview

```
[ Internet ] ──── HTTPS (443) ────► [ EC2: Caddy (SSL & Reverse Proxy) ]
                                              │
                     ┌────────────────────────┼────────────────────────┐
                     ▼                        ▼                        ▼
           [ User Service :8000 ]   [ Main Service :8001 ]   [ AI Interviewer API :8000 ]
                     │                        │                        │
                     │                        │              [ AI Voice Worker ]
                     │                        │              [ AI Analysis Worker ]
                     └────────────────────────┼────────────────────────┘
                                              ▼
                        ┌───────────────────────────────────────────┐
                        │ Internal Docker Network (thinkaloud-net)  │
                        │  - Redis 7 (Port 6379, In-Memory/PubSub)  │
                        │  - RabbitMQ (Port 5672, Durable Queues)   │
                        │  - Datadog Agent (Port 8125/8126 APM)     │
                        └───────────────────────────────────────────┘
                                              │
                      Private VPC (Port 5432) │
                                              ▼
                             [ Amazon RDS PostgreSQL 16 ]
                             ├── database: user_service
                             ├── database: main_service
                             └── database: interviewer_service
```

---

## 2. Infrastructure & Sizing Specifications

### EC2 Sizing:
- **Recommended**: **`c7g.xlarge`** (4 vCPUs, 8 GB RAM, AWS Graviton3) or **`c6i.xlarge`** (4 vCPUs, 8 GB RAM, Intel x86) — ~$100/mo.
- **Budget / Minimum**: **`t4g.large`** (2 vCPUs, 8 GB RAM) — ~$49/mo (enable Unlimited CPU credit mode).
- **Storage**: 40 GB gp3 SSD (3,000 IOPS, 125 MB/s).
- **Swap**: 4 GB swap file on the EBS volume.

### RDS PostgreSQL Sizing:
- **Instance**: `db.t4g.small` (2 vCPU, 2 GB RAM) or `db.t4g.micro` (Free Tier).
- **Storage**: 20 GB gp3 with storage autoscaling enabled.
- **Databases to create in RDS**:
  1. `user_service`
  2. `main_service`
  3. `interviewer_service`

---

## 3. Security Groups Configuration

### EC2 Security Group:
- **Port 80 (HTTP)**: `0.0.0.0/0` (for ACME TLS certificates)
- **Port 443 (HTTPS)**: `0.0.0.0/0` (public API / frontend requests)
- **Port 22 (SSH)**: `Your-IP-Only` (or use AWS SSM Session Manager)
- *All internal ports (`5672`, `6379`, `8000`, `8001`, `8002`, `15672`)* are strictly closed to the public internet and only accessible via Docker internal network.

### RDS PostgreSQL Security Group:
- **Port 5432 (PostgreSQL)**: Source = `EC2-Security-Group-ID` (never public).

---

## 4. Deployment Steps on the EC2 Instance

### Step 1: Install Docker & Docker Compose
```bash
sudo apt update && sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker ubuntu
newgrp docker
```

### Step 2: Configure 4GB Swap Space
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Step 3: Clone Repository & Configure Environment
```bash
git clone https://github.com/itsVish16/ThinkAloudAI.git
cd ThinkAloudAI/Backend
cp .env.example .env
```

Edit `.env` and set your real credentials:
```env
# 1. Domain & SSL
API_DOMAIN=api.thinkaloudai.tech
ACME_EMAIL=admin@thinkaloudai.tech
CORS_ALLOWED_ORIGINS=https://thinkaloudai.tech,https://www.thinkaloudai.tech

# 2. Amazon RDS PostgreSQL Connection Strings
USER_SERVICE_DATABASE_URL=postgresql+asyncpg://<RDS_USER>:<RDS_PASS>@<RDS_ENDPOINT>:5432/user_service
MAIN_SERVICE_DATABASE_URL=postgresql+asyncpg://<RDS_USER>:<RDS_PASS>@<RDS_ENDPOINT>:5432/main_service
INTERVIEWER_SERVICE_DATABASE_URL=postgresql+asyncpg://<RDS_USER>:<RDS_PASS>@<RDS_ENDPOINT>:5432/interviewer_service

# 3. Security (MUST be identical across all services)
JWT_SECRET_KEY=generate_a_random_64_character_hex_secret_here

# 4. LiveKit WebRTC Cloud
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret

# 5. AI Providers
SARVAM_API_KEY=your_sarvam_key
FIREWORKS_API_KEY=your_fireworks_key
```

### Step 4: Launch Production Stack
```bash
bash deploy.sh
# Or manually:
docker compose -f docker-compose.prod.yml up -d --build
```

### Step 5: Verify Running Health Status
```bash
docker compose -f docker-compose.prod.yml ps
```

---

## 5. Health Endpoints & Diagnostics

- **Public HTTPS Gateway**: `https://api.thinkaloudai.tech/`
- **User Service Health**: `https://api.thinkaloudai.tech/health/ready`
- **Main Service Health**: `https://api.thinkaloudai.tech/`
- **AI Interviewer Health**: `https://api.thinkaloudai.tech/api/interview-types`
- **RabbitMQ Management**: Port 15672 (via SSH tunnel: `ssh -L 15672:localhost:15672 ubuntu@<EC2_IP>`)

---

## 6. Updating Code in Production

To update the running production services with zero hassle:
```bash
cd Backend
git pull
docker compose -f docker-compose.prod.yml up -d --build
```
