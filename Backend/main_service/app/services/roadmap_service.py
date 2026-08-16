from typing import List
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from sqlalchemy.orm import selectinload

from app.models.roadmap import Roadmap, RoadmapTopic, RoadmapItem
from app.schemas.roadmap import (
    RoadmapCreate,
    RoadmapOut,
    RoadmapTopicCreate,
    ScheduledInterviewOut,
)


class RoadmapService:
    @staticmethod
    async def get_scheduled_interviews(db: AsyncSession, user_id: str) -> List[ScheduledInterviewOut]:
        query = (
            select(RoadmapItem, RoadmapTopic, Roadmap)
            .join(RoadmapTopic, RoadmapItem.topic_id == RoadmapTopic.id)
            .join(Roadmap, RoadmapTopic.roadmap_id == Roadmap.id)
            .filter(RoadmapItem.content_type == "mock_interview")
            .filter(Roadmap.user_id == user_id)
            .filter(RoadmapItem.is_completed == False)
            .order_by(Roadmap.created_at.desc())
        )
        result = await db.execute(query)

        scheduled_interviews = []
        for item, topic, roadmap in result.all():
            scheduled_interviews.append(
                ScheduledInterviewOut(
                    id=item.id,
                    topic_id=item.topic_id,
                    title=item.title,
                    content_type=item.content_type,
                    content_id=item.content_id,
                    timeline_days=item.timeline_days,
                    is_completed=item.is_completed,
                    roadmap_title=roadmap.title,
                    topic_title=topic.title,
                    roadmap_id=roadmap.id,
                )
            )
        return scheduled_interviews

    @staticmethod
    async def get_user_roadmaps(db: AsyncSession, user_id: str) -> List[Roadmap]:
        query = select(Roadmap).filter(Roadmap.user_id == user_id).order_by(Roadmap.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_roadmap(roadmap_id: int, db: AsyncSession, user_id: str) -> Roadmap:
        query = (
            select(Roadmap)
            .options(selectinload(Roadmap.topics).selectinload(RoadmapTopic.items))
            .filter(Roadmap.id == roadmap_id)
            .filter(or_(Roadmap.user_id == user_id, Roadmap.is_general == True))
        )
        result = await db.execute(query)
        roadmap = result.scalars().first()
        if not roadmap:
            raise HTTPException(status_code=404, detail="Roadmap not found")
        return roadmap

    @staticmethod
    async def create_roadmap(request: RoadmapCreate, db: AsyncSession, user_id: str) -> Roadmap:
        roadmap = Roadmap(
            user_id=user_id,
            title=request.title,
            description=request.description,
            is_general=False,
        )
        db.add(roadmap)
        await db.flush()

        for topic_in in request.topics:
            topic = RoadmapTopic(
                roadmap_id=roadmap.id,
                title=topic_in.title,
                order=topic_in.order,
            )
            db.add(topic)
            await db.flush()

            for item_in in topic_in.items:
                item = RoadmapItem(
                    topic_id=topic.id,
                    title=item_in.title,
                    content_type=item_in.content_type,
                    content_id=item_in.content_id,
                    timeline_days=item_in.timeline_days,
                    is_completed=False,
                )
                db.add(item)

        await db.commit()
        return await RoadmapService.get_roadmap(roadmap.id, db, user_id)

    @staticmethod
    async def toggle_item(item_id: int, is_completed: bool, db: AsyncSession, user_id: str) -> dict:
        query = (
            select(RoadmapItem)
            .join(RoadmapTopic, RoadmapItem.topic_id == RoadmapTopic.id)
            .join(Roadmap, RoadmapTopic.roadmap_id == Roadmap.id)
            .filter(RoadmapItem.id == item_id)
            .filter(Roadmap.user_id == user_id)
        )
        result = await db.execute(query)
        item = result.scalars().first()
        if not item:
            raise HTTPException(status_code=404, detail="Roadmap item not found")

        item.is_completed = is_completed
        await db.commit()
        return {"status": "success", "item_id": item_id, "is_completed": is_completed}

    @staticmethod
    async def delete_roadmap(roadmap_id: int, db: AsyncSession, user_id: str) -> dict:
        query = select(Roadmap).filter(Roadmap.id == roadmap_id, Roadmap.user_id == user_id)
        result = await db.execute(query)
        roadmap = result.scalars().first()
        if not roadmap:
            raise HTTPException(status_code=404, detail="Roadmap not found")

        await db.delete(roadmap)
        await db.commit()
        return {"status": "success", "message": f"Roadmap {roadmap_id} deleted"}
