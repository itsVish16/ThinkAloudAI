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
    json_path = os.path.join(os.path.dirname(__file__), "..", "canonical_dsa_questions.json")
    if not os.path.exists(json_path):
        json_path = os.path.join(os.path.dirname(__file__), "canonical_dsa_questions.json")
        if not os.path.exists(json_path):
            logger.warning(f"File {json_path} not found. Skipping DSA seed.")
            return

    with open(json_path, "r", encoding="utf-8") as f:
        questions_data = json.load(f)

    inserted, updated = 0, 0
    for data in questions_data:
        title = data.get("title")
        if not title:
            continue
        try:
            tags = data.pop("tags", [])
            result = await db.execute(select(DSAQuestion).filter(DSAQuestion.title == title))
            existing_q = result.scalars().first()

            if existing_q:
                existing_q.description = data.get("description", existing_q.description)
                existing_q.difficulty = data.get("difficulty", existing_q.difficulty)
                existing_q.function_name = data.get("function_name", existing_q.function_name)
                existing_q.python_starter_code = data.get("python_starter_code", existing_q.python_starter_code)
                existing_q.cpp_starter_code = data.get("cpp_starter_code", existing_q.cpp_starter_code)
                existing_q.cpp_test_harness = data.get("cpp_test_harness", existing_q.cpp_test_harness)
                existing_q.test_cases = data.get("test_cases", existing_q.test_cases)
                existing_q.hints = data.get("hints", existing_q.hints)
                existing_q.optimal_time_complexity = data.get("optimal_time_complexity", existing_q.optimal_time_complexity)
                existing_q.optimal_space_complexity = data.get("optimal_space_complexity", existing_q.optimal_space_complexity)
                q_id = existing_q.id
                updated += 1
            else:
                new_q = DSAQuestion(**data)
                db.add(new_q)
                await db.flush()
                q_id = new_q.id
                inserted += 1

            if tags:
                existing_tags_res = await db.execute(select(ProblemTag).filter(ProblemTag.question_id == q_id))
                existing_tags = {t.tag_name for t in existing_tags_res.scalars().all()}
                for tag_name in tags:
                    if tag_name not in existing_tags:
                        db.add(ProblemTag(question_id=q_id, tag_name=tag_name))

        except Exception as ex:
            logger.error(f"Error seeding DSA item {title}: {ex}")

    await db.commit()
    logger.info(f"✅ Canonical DSA Questions Seeded: {inserted} inserted, {updated} updated (Total: {len(questions_data)}).")


async def seed_system_design_questions(db):
    from scripts.generate_system_design_md import SYSTEM_DESIGN_TOPICS

    inserted, updated = 0, 0
    for topic in SYSTEM_DESIGN_TOPICS:
        title = topic["title"]
        domain = topic.get("domain", topic.get("category", "Backend / Distributed Systems"))
        role = topic.get("role", "Senior Software Engineer")

        desc_parts = [
            f"> **Summary:** {topic['summary']}\n",
            "### 1. Requirements & Scope",
            "**Functional Requirements:**",
            "\n".join(f"- {r}" for r in topic["functional_reqs"]),
            "\n**Non-Functional Requirements:**",
            "\n".join(f"- {r}" for r in topic["non_functional_reqs"]),
            "\n### 2. Capacity & Back-of-the-Envelope Estimations",
            topic["estimations"],
            "\n### 3. High-Level Architecture",
            topic["architecture_diagram"],
            "\n### 4. Data Model & Database Design",
            topic["data_model"]
        ]
        if "deep_dive" in topic:
            desc_parts.extend([
                "\n### 5. Technical Deep Dive & Key Trade-offs",
                topic["deep_dive"]
            ])

        full_description = "\n\n".join(desc_parts)

        res = await db.execute(select(SystemDesignQuestion).filter(SystemDesignQuestion.title == title))
        existing_q = res.scalars().first()

        if existing_q:
            existing_q.description = full_description
            existing_q.domain = domain
            existing_q.role = role
            updated += 1
        else:
            new_q = SystemDesignQuestion(
                title=title,
                description=full_description,
                domain=domain,
                role=role
            )
            db.add(new_q)
            inserted += 1

    await db.commit()
    logger.info(f"✅ System Design Questions Seeded: {inserted} inserted, {updated} updated (Total: {len(SYSTEM_DESIGN_TOPICS)}).")


async def seed_behavioral_questions(db):
    b_questions = [
        {
            "title": "Handling Critical Production Outage Under Pressure",
            "description": "Tell me about a time when a critical system failed in production. Walk me through how you triaged the issue, communicated with stakeholders, coordinated the fix, and implemented preventive safeguards afterwards.",
            "category": "Ownership & Crisis Management"
        },
        {
            "title": "Disagreement with Engineering Leadership on Technical Direction",
            "description": "Describe a situation where you strongly disagreed with a team lead, architect, or peer on a technical decision or architecture choice. How did you advocate for your perspective with data, evaluate trade-offs, and what was the ultimate resolution?",
            "category": "Collaboration & Conflict Resolution"
        },
        {
            "title": "Delivering a Major Feature with Ambiguous Requirements",
            "description": "Tell me about a high-impact project you delivered where the initial requirements were vague or rapidly changing. How did you break down milestones, scope MVPs, align cross-functional stakeholders, and guarantee on-time delivery?",
            "category": "Execution & Navigating Ambiguity"
        },
        {
            "title": "Overcoming a Project Failure or Critical Mistake",
            "description": "Can you share an experience where a project failed to meet expectations or a code change caused a significant regression? How did you take ownership of the mistake, communicate with your team, and what concrete lessons did you apply to future projects?",
            "category": "Accountability & Continuous Learning"
        },
        {
            "title": "Balancing Technical Debt Refactoring vs Tight Product Deadlines",
            "description": "Describe a time when you had to balance paying down critical technical debt with aggressive product feature deadlines. How did you negotiate priorities with product managers and ensure code health without slowing business momentum?",
            "category": "Technical Judgment & Prioritization"
        },
        {
            "title": "Pushing Back on Unrealistic Deadlines or Scope Creep",
            "description": "Tell me about a time when you were asked to deliver an unrealistic project scope within a tight timeframe. How did you push back constructively, present technical constraints, and renegotiate deliverables or timelines?",
            "category": "Stakeholder Management & Integrity"
        },
        {
            "title": "Mentoring a Teammate and Elevating Engineering Quality",
            "description": "Share an example where you mentored a junior engineer, paired with a struggling teammate, or elevated engineering quality on your team (e.g., automated testing, code review standards). What coaching approach did you use, and what was the measurable outcome?",
            "category": "Leadership & Team Enablement"
        },
        {
            "title": "Simplifying Complex Legacy Architecture to Boost Reliability",
            "description": "Describe a time when you identified unnecessary complexity or fragile legacy code and proactively simplified it. What was your strategy for safe refactoring without downtime, and what was the impact on latency, maintainability, or cloud costs?",
            "category": "Invent & Simplify"
        },
        {
            "title": "Driving Cross-Functional Alignment Across Teams",
            "description": "Tell me about a project that required close collaboration across multiple engineering squads, product managers, designers, or external vendors. How did you resolve communication bottlenecks and keep everyone aligned toward a common goal?",
            "category": "Cross-Functional Collaboration"
        },
        {
            "title": "Making High-Impact Architectural Decisions with Incomplete Data",
            "description": "Describe a scenario where you had to make a critical architectural or toolchain decision with incomplete or imperfect information under a tight deadline. How did you evaluate trade-offs, mitigate downside risks, and validate your choice?",
            "category": "Bias for Action & Decision Making"
        },
        {
            "title": "Receiving Tough Constructive Feedback and Transforming It",
            "description": "Can you share a time when you received difficult constructive feedback from a manager, peer, or client? How did you process the feedback, what specific behavior or workflow did you change, and how did it improve your impact?",
            "category": "Self-Awareness & Growth Mindset"
        },
        {
            "title": "Resolving a Frustrating Team Conflict Amicably",
            "description": "Tell me about a situation where communication broke down or frustration arose between team members during a high-stress release. How did you de-escalate the tension, foster empathy, and find a productive middle ground?",
            "category": "Emotional Intelligence & Conflict Management"
        },
        {
            "title": "Going Above and Beyond to Unblock Customers or Team",
            "description": "Share an example where you took initiative outside your formal job responsibilities to solve an unowned problem, fix a customer pain point, or unblock other engineers. What motivated you and what was the long-term impact?",
            "category": "Extreme Ownership"
        },
        {
            "title": "Advocating for Security and Scalability Under Pressure",
            "description": "Describe a situation where there was intense business pressure to cut corners on security, data validation, or testing. How did you champion engineering excellence and ensure system safety without becoming a blocker?",
            "category": "Engineering Standards & Ethics"
        },
        {
            "title": "Prioritizing Competing Urgent Production Tasks",
            "description": "Tell me about a day or week where multiple urgent production bugs, customer escalations, and feature deadlines landed on your plate at once. How did you triage, delegate, communicate status, and maintain focus under pressure?",
            "category": "Time Management & Resilience"
        },
        {
            "title": "Rapidly Mastering a New Technology or Domain to Ship",
            "description": "Describe a project where you were tasked with building in a completely unfamiliar programming language, framework, or domain on short notice. How did you structure your learning, prototype quickly, and deliver a production-ready solution?",
            "category": "Learn & Be Curious"
        }
    ]

    inserted, updated = 0, 0
    for item in b_questions:
        res = await db.execute(select(BehavioralQuestion).filter(BehavioralQuestion.title == item["title"]))
        existing = res.scalars().first()
        if existing:
            existing.description = item["description"]
            existing.category = item["category"]
            updated += 1
        else:
            db.add(BehavioralQuestion(**item))
            inserted += 1

    await db.commit()
    logger.info(f"✅ Behavioral Questions Seeded: {inserted} inserted, {updated} updated (Total: {len(b_questions)}).")


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
