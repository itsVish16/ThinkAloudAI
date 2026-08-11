"""seed_core_questions

Revision ID: 948644a8b081
Revises: dce905768024
Create Date: 2026-08-11 19:24:24.221549

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '948644a8b081'
down_revision: Union[str, Sequence[str], None] = 'dce905768024'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO system_design_questions (title, description, domain, role, created_at) VALUES 
        ('Design a Distributed Message Queue', 'Design a distributed message queue system like Apache Kafka or RabbitMQ. Focus on partitioning, replication, message durability, and consumer groups.', 'Backend', 'Senior Software Engineer', NOW()),
        ('Design a URL Shortener', 'Design a scalable URL shortener like bit.ly. Focus on collision prevention, capacity estimation, caching strategies, and highly available reads.', 'Backend', 'Software Engineer', NOW()),
        ('Design a Recommendation System for Netflix', 'Design a video recommendation system. Focus on the ML pipeline, feature store, real-time vs batch inference, and model serving infrastructure.', 'AI/ML', 'Senior Software Engineer', NOW()),
        ('Design a RAG-based Customer Support Chatbot', 'Design a Retrieval-Augmented Generation (RAG) customer support agent. Discuss vector database scaling, embedding generation, context window management, and handling hallucinations.', 'AI/ML', 'Software Engineer', NOW());
    """)

    op.execute("""
        INSERT INTO behavioral_questions (title, description, category, created_at) VALUES 
        ('Handling Conflict', 'Tell me about a time you had a conflict with a coworker or manager and how you resolved it. Focus on communication, empathy, and professional resolution.', 'Conflict', NOW()),
        ('Overcoming Failure', 'Tell me about a time a project you were working on failed or missed a deadline. What happened and what did you learn?', 'Resilience', NOW()),
        ('Taking Initiative', 'Tell me about a time you identified a problem and took the initiative to solve it without being asked.', 'Leadership', NOW());
    """)

    op.execute("""
        INSERT INTO pm_questions (title, description, category, created_at) VALUES 
        ('Improve Google Maps', 'How would you improve Google Maps for a specific user segment? Identify the segment, their pain points, and propose 3 feature ideas.', 'Product Sense', NOW()),
        ('Pricing a New SaaS Product', 'You are launching a new B2B SaaS product for small businesses. How do you determine the pricing model?', 'Strategy', NOW()),
        ('Metrics for Airbnb', 'What are the top 3 metrics you would track for Airbnb''s host experience? Why?', 'Execution', NOW());
    """)

    op.execute("""
        INSERT INTO aiml_questions (title, description, domain, created_at) VALUES 
        ('Explain Transformer Architecture', 'Explain the self-attention mechanism in the Transformer architecture and why it is more efficient than RNNs for sequence modeling.', 'Deep Learning', NOW()),
        ('Handling Imbalanced Data', 'You are building a fraud detection model where only 0.1% of transactions are fraudulent. How do you handle this class imbalance?', 'MLOps', NOW()),
        ('Deploying LLMs in Production', 'What are the key challenges when deploying large language models in production? Discuss latency, cost, and quantization techniques.', 'Generative AI', NOW());
    """)


def downgrade() -> None:
    """Downgrade schema."""
    pass
