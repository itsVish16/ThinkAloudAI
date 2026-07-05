from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from sqlalchemy.orm import selectinload
from typing import List

from app.database import get_db
from app.models.roadmap import Roadmap, RoadmapTopic, RoadmapItem
from app.schemas.roadmap import (
    RoadmapCreate, 
    RoadmapOut, 
    RoadmapItemOut,
    RoadmapTopicCreate
)

router = APIRouter(prefix="/roadmaps", tags=["Roadmaps"])

def get_current_user_id() -> str:
    return "test_user_id"

@router.get("", response_model=List[RoadmapOut])
async def get_user_roadmaps(db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """Retrieve all roadmaps for the current user and general roadmaps."""
    query = (
        select(Roadmap)
        .options(
            selectinload(Roadmap.topics).selectinload(RoadmapTopic.items)
        )
        .filter(or_(Roadmap.user_id == user_id, Roadmap.is_general == True))
        .order_by(Roadmap.created_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{roadmap_id}", response_model=RoadmapOut)
async def get_roadmap(roadmap_id: int, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """Retrieve a specific roadmap with all its topics and items."""
    query = (
        select(Roadmap)
        .options(
            selectinload(Roadmap.topics).selectinload(RoadmapTopic.items)
        )
        .filter(Roadmap.id == roadmap_id)
        .filter(or_(Roadmap.user_id == user_id, Roadmap.is_general == True))
    )
    result = await db.execute(query)
    roadmap = result.scalars().first()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    return roadmap

@router.post("/", response_model=RoadmapOut)
async def create_roadmap(request: RoadmapCreate, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """Create a new roadmap with nested topics and items."""
    roadmap = Roadmap(
        user_id=user_id,
        title=request.title,
        description=request.description,
        is_general=False
    )
    db.add(roadmap)
    await db.flush()
    
    for topic_in in request.topics:
        topic = RoadmapTopic(
            roadmap_id=roadmap.id,
            title=topic_in.title,
            order_index=topic_in.order_index
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
                is_completed=item_in.is_completed
            )
            db.add(item)
            
    await db.commit()
    await db.refresh(roadmap)
    
    # Reload with relationships
    query = select(Roadmap).options(selectinload(Roadmap.topics).selectinload(RoadmapTopic.items)).filter(Roadmap.id == roadmap.id)
    result = await db.execute(query)
    return result.scalars().first()

@router.post("/{roadmap_id}/topics/{topic_id}/items/{item_id}/toggle", response_model=RoadmapItemOut)
async def toggle_item_completion(roadmap_id: int, topic_id: int, item_id: int, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """Toggle the completion status of a specific roadmap item."""
    query = select(Roadmap).filter(Roadmap.id == roadmap_id, Roadmap.user_id == user_id)
    result = await db.execute(query)
    roadmap = result.scalars().first()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found or not owned by user")
        
    query = select(RoadmapItem).filter(
        RoadmapItem.id == item_id,
        RoadmapItem.topic_id == topic_id
    )
    result = await db.execute(query)
    item = result.scalars().first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    item.is_completed = not item.is_completed
    await db.commit()
    await db.refresh(item)
    return item

@router.delete("/{roadmap_id}")
async def delete_roadmap(roadmap_id: int, db: AsyncSession = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    """Delete a roadmap and all nested items."""
    query = select(Roadmap).filter(Roadmap.id == roadmap_id, Roadmap.user_id == user_id)
    result = await db.execute(query)
    roadmap = result.scalars().first()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found or not owned by user")
        
    await db.delete(roadmap)
    await db.commit()
    return {"message": "Roadmap deleted successfully"}
