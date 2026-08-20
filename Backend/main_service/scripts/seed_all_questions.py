import asyncio
import json
import logging
import os
import sys
from sqlalchemy.future import select

# Ensure app package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, engine, Base
from app.models.dsa import DSAQuestion, ProblemTag
from app.models.system_design import SystemDesignQuestion
from app.models.behavioral import BehavioralQuestion
from app.models.product_management import PMQuestion
from app.models.aiml import AIMLQuestion

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


async def seed_dsa_questions(db):
    jsonl_path = os.path.join(os.path.dirname(__file__), "enriched_leetcode.jsonl")
    if not os.path.exists(jsonl_path):
        logger.warning(f"File {jsonl_path} not found. Skipping JSONL DSA seed.")
        return

    with open(jsonl_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    inserted, updated = 0, 0
    for line in lines:
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            title = data.get("title")
            if not title:
                continue

            result = await db.execute(select(DSAQuestion).filter(DSAQuestion.title == title))
            existing_q = result.scalars().first()

            tc_data = data.get("test_cases", [])
            test_cases_str = tc_data if isinstance(tc_data, str) else json.dumps(tc_data)

            if existing_q:
                existing_q.description = data.get("description", existing_q.description)
                existing_q.difficulty = data.get("difficulty", existing_q.difficulty)
                existing_q.function_name = data.get("function_name", existing_q.function_name)
                existing_q.python_starter_code = data.get("python_starter_code", existing_q.python_starter_code)
                existing_q.hints = json.dumps(data.get("hints", []))
                existing_q.test_cases = test_cases_str
                q_id = existing_q.id
                updated += 1
            else:
                new_q = DSAQuestion(
                    title=title,
                    description=data.get("description", ""),
                    difficulty=data.get("difficulty", "Medium"),
                    function_name=data.get("function_name", "solution"),
                    python_starter_code=data.get("python_starter_code", ""),
                    hints=json.dumps(data.get("hints", [])),
                    test_cases=test_cases_str,
                )
                db.add(new_q)
                await db.flush()
                q_id = new_q.id
                inserted += 1

            tags = data.get("tags", [])
            if tags:
                await db.execute(ProblemTag.__table__.delete().where(ProblemTag.question_id == q_id))
                for tag_name in tags:
                    db.add(ProblemTag(question_id=q_id, tag_name=tag_name))

        except Exception as ex:
            logger.error(f"Error seeding DSA item: {ex}")

    await db.commit()
    logger.info(f"✅ DSA Questions Seeded: {inserted} inserted, {updated} updated.")


async def seed_system_design_questions(db):
    sd_questions = [
        {
            "title": "Design a Distributed Message Queue",
            "description": "Design a distributed, highly available message broker like Apache Kafka or RabbitMQ. Discuss topic partitioning, log compaction, offset commit semantics, replication, leader election, and consumer group rebalancing under high network throughput.",
            "domain": "Backend",
            "role": "Senior Software Engineer"
        },
        {
            "title": "Design a High-Throughput URL Shortener",
            "description": "Design a globally distributed URL shortening service like TinyURL / bit.ly capable of handling 100M new URLs/month and 10B clicks/month. Detail Base62 encoding, custom aliases, collision resolution, multi-tier caching (Redis), database sharding, and analytics tracking.",
            "domain": "Backend",
            "role": "Software Engineer"
        },
        {
            "title": "Design a Real-Time Collaborative Document Editor",
            "description": "Design Google Docs / Notion collaborative editor supporting concurrent edits with sub-100ms latency. Explain Operational Transformation (OT) vs CRDTs (Conflict-free Replicated Data Types), WebSockets connection multiplexing, document snapshotting, and presence awareness.",
            "domain": "Full-Stack / Distributed Systems",
            "role": "Staff Software Engineer"
        },
        {
            "title": "Design a Video Streaming Platform (Netflix / YouTube)",
            "description": "Design a video ingestion and streaming pipeline. Cover chunking, adaptive bitrate streaming (HLS/DASH), CDN edge caching strategies, transcoding workers, metadata indexing, and global multi-region failover.",
            "domain": "Cloud & Infrastructure",
            "role": "Senior Infrastructure Engineer"
        },
        {
            "title": "Design a Retrieval-Augmented Generation (RAG) Architecture",
            "description": "Design an enterprise-scale RAG system with low-latency search and real-time document ingestion. Address embedding models, approximate nearest neighbor (HNSW) vector indexing, hybrid BM25 + dense retrieval, reranking, context window optimization, and prompt injection defense.",
            "domain": "AI/ML",
            "role": "AI/ML Systems Engineer"
        },
        {
            "title": "Design a Real-Time Ride Hailing Service (Uber / Lyft)",
            "description": "Design the geospatial matchmaking and dispatch engine for a ride-hailing app. Discuss QuadTree vs Google S2 / Uber H3 spatial indexing, real-time driver telemetry streaming over WebSockets, dynamic surge pricing algorithms, and trip state machines.",
            "domain": "Backend",
            "role": "Senior Software Engineer"
        }
    ]

    inserted = 0
    for item in sd_questions:
        res = await db.execute(select(SystemDesignQuestion).filter(SystemDesignQuestion.title == item["title"]))
        if not res.scalars().first():
            db.add(SystemDesignQuestion(**item))
            inserted += 1

    await db.commit()
    logger.info(f"✅ System Design Questions Seeded: {inserted} new questions added.")


async def seed_behavioral_questions(db):
    b_questions = [
        {
            "title": "Handling Critical Production Outage Under Pressure",
            "description": "Tell me about a time when a critical system failed in production. Walk me through how you triaged the issue, communicated with stakeholders, coordinated the fix, and implemented preventive safeguards afterwards.",
            "category": "Ownership & Crisis Management"
        },
        {
            "title": "Disagreement with Engineering Leadership on Technical Direction",
            "description": "Describe a situation where you strongly disagreed with a team lead or architect on a technical decision or architecture choice. How did you advocate for your perspective, evaluate trade-offs, and what was the ultimate resolution?",
            "category": "Have Backbone; Disagree & Commit"
        },
        {
            "title": "Delivering a Major Feature with Ambiguous Requirements",
            "description": "Tell me about a high-impact project you delivered where the initial requirements were vague or rapidly changing. How did you define milestones, scope MVPs, align cross-functional teams, and guarantee delivery?",
            "category": "Deliver Results & Bias for Action"
        },
        {
            "title": "Mentoring and Elevating Team Performance",
            "description": "Share an example where you mentored a junior engineer or helped a struggling teammate succeed. What coaching strategies did you use, and how did it impact the team's engineering velocity?",
            "category": "People & Leadership"
        },
        {
            "title": "Simplifying a Complex Legacy Architecture",
            "description": "Describe a time when you identified unnecessary complexity or technical debt in a codebase and proactively simplified it. What was the impact on latency, maintainability, or infrastructure costs?",
            "category": "Invent & Simplify"
        }
    ]

    inserted = 0
    for item in b_questions:
        res = await db.execute(select(BehavioralQuestion).filter(BehavioralQuestion.title == item["title"]))
        if not res.scalars().first():
            db.add(BehavioralQuestion(**item))
            inserted += 1

    await db.commit()
    logger.info(f"✅ Behavioral Questions Seeded: {inserted} new questions added.")


async def seed_pm_questions(db):
    pm_questions = [
        {
            "title": "Design a New Feature for Spotify to Improve Social Discovery",
            "description": "How would you design a social music discovery feature for Spotify? Walk through user personas, pain points, core user flows, monetization vs engagement trade-offs, and key North Star metrics (e.g., DAU/MAU, 30-day retention).",
            "category": "Product Sense & Design"
        },
        {
            "title": "Diagnosing a 15% Drop in E-Commerce Checkout Conversion",
            "description": "Imagine your e-commerce platform experienced a 15% decline in cart checkout completion over the last week. How would you systematically diagnose the root cause across user funnels, tech latency, marketing channels, and fraud filters?",
            "category": "Execution & Analytics"
        },
        {
            "title": "Pricing Strategy and Launch for a B2B Developer API",
            "description": "You are the PM launching a new real-time AI voice API product. How would you decide on tiered pricing (pay-as-you-go vs committed usage), determine free tier quotas, and plan go-to-market developer relations?",
            "category": "Strategy & Monetization"
        }
    ]

    inserted = 0
    for item in pm_questions:
        res = await db.execute(select(PMQuestion).filter(PMQuestion.title == item["title"]))
        if not res.scalars().first():
            db.add(PMQuestion(**item))
            inserted += 1

    await db.commit()
    logger.info(f"✅ Product Management Questions Seeded: {inserted} new questions added.")


async def seed_aiml_questions(db):
    aiml_questions = [
        {
            "title": "Fine-Tuning vs RAG Trade-offs for Enterprise LLM Applications",
            "description": "When should an enterprise choose LoRA / QLoRA fine-tuning versus Retrieval-Augmented Generation (RAG)? Discuss knowledge freshness, training costs, data privacy, latency constraints, and hallucination reduction.",
            "domain": "Generative AI & LLMs",
            "role": "AI Engineer / LLM Specialist"
        },
        {
            "title": "Scaling Real-Time LLM Inference with Speculative Decoding & KV Caching",
            "description": "Explain techniques used to optimize Time-To-First-Token (TTFT) and token generation throughput for Large Language Models. Detail PagedAttention, KV-cache quantization (FP8/INT4), continuous batching (vLLM), and speculative decoding.",
            "domain": "ML Systems & Inference",
            "role": "Machine Learning Engineer"
        },
        {
            "title": "Handling Data Drift and Covariate Shift in Production ML Models",
            "description": "How do you detect and mitigate statistical data drift and concept drift in a live fraud-detection model? Discuss PSI (Population Stability Index), KS-tests, online retraining pipelines, and shadow model deployment.",
            "domain": "MLOps",
            "role": "Senior MLOps Engineer"
        }
    ]

    inserted = 0
    for item in aiml_questions:
        res = await db.execute(select(AIMLQuestion).filter(AIMLQuestion.title == item["title"]))
        if not res.scalars().first():
            db.add(AIMLQuestion(**item))
            inserted += 1

    await db.commit()
    logger.info(f"✅ AI/ML Questions Seeded: {inserted} new questions added.")


async def main():
    logger.info("🚀 Starting comprehensive question seeding across all domains...")
    async with SessionLocal() as db:
        await seed_dsa_questions(db)
        await seed_system_design_questions(db)
        await seed_behavioral_questions(db)
        await seed_pm_questions(db)
        await seed_aiml_questions(db)

    # Invalidate Redis question cache
    try:
        from app.database import redis_client
        async for key in redis_client.scan_iter("dsa:questions:all:*"):
            await redis_client.delete(key)
        logger.info("🧹 Redis question caches cleared.")
    except Exception as e:
        logger.warning(f"Could not clear Redis cache: {e}")

    logger.info("🎉 All question banks seeded successfully!")


if __name__ == "__main__":
    asyncio.run(main())
