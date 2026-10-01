from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import (
    Project,
    ProjectBookmark,
    ProjectFollow,
    ProjectLike,
    ProjectTechnology,
    ReputationEvent,
    User,
)
from app.schemas.project_engagement import EngagementResponse, TechnologyCreate

router = APIRouter(prefix="/api/projects", tags=["Project Engagement"])


def get_project(project_id: int, db: Session) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def record_event(db: Session, user: User, project_id: int, event_type: str, points: int) -> None:
    db.add(ReputationEvent(user_id=user.id, project_id=project_id, event_type=event_type, points=points))


@router.get("/{project_id}/engagement", response_model=EngagementResponse)
def engagement(project_id: int, db: Session = Depends(get_db), user: User | None = Depends(get_current_user)):
    get_project(project_id, db)
    likes = db.scalar(select(func.count(ProjectLike.id)).where(ProjectLike.project_id == project_id)) or 0
    bookmarks = db.scalar(select(func.count(ProjectBookmark.id)).where(ProjectBookmark.project_id == project_id)) or 0
    followers = db.scalar(select(func.count(ProjectFollow.id)).where(ProjectFollow.project_id == project_id)) or 0
    return {
        "project_id": project_id,
        "likes": likes,
        "bookmarks": bookmarks,
        "followers": followers,
        "liked": bool(user and db.scalar(select(ProjectLike.id).where(ProjectLike.project_id == project_id, ProjectLike.user_id == user.id))),
        "bookmarked": bool(user and db.scalar(select(ProjectBookmark.id).where(ProjectBookmark.project_id == project_id, ProjectBookmark.user_id == user.id))),
        "followed": bool(user and db.scalar(select(ProjectFollow.id).where(ProjectFollow.project_id == project_id, ProjectFollow.user_id == user.id))),
    }


@router.post("/{project_id}/like", response_model=EngagementResponse)
def toggle_like(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_project(project_id, db)
    item = db.scalar(select(ProjectLike).where(ProjectLike.project_id == project_id, ProjectLike.user_id == user.id))
    if item:
        db.delete(item)
    else:
        db.add(ProjectLike(project_id=project_id, user_id=user.id))
        record_event(db, user, project_id, "project.liked", 2)
    db.commit()
    return engagement(project_id, db, user)


@router.post("/{project_id}/bookmark", response_model=EngagementResponse)
def toggle_bookmark(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_project(project_id, db)
    item = db.scalar(select(ProjectBookmark).where(ProjectBookmark.project_id == project_id, ProjectBookmark.user_id == user.id))
    if item:
        db.delete(item)
    else:
        db.add(ProjectBookmark(project_id=project_id, user_id=user.id))
        record_event(db, user, project_id, "project.bookmarked", 1)
    db.commit()
    return engagement(project_id, db, user)


@router.post("/{project_id}/follow", response_model=EngagementResponse)
def toggle_follow(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_project(project_id, db)
    item = db.scalar(select(ProjectFollow).where(ProjectFollow.project_id == project_id, ProjectFollow.user_id == user.id))
    if item:
        db.delete(item)
    else:
        db.add(ProjectFollow(project_id=project_id, user_id=user.id))
        record_event(db, user, project_id, "project.followed", 3)
    db.commit()
    return engagement(project_id, db, user)


@router.post("/{project_id}/technologies")
def add_technology(project_id: int, payload: TechnologyCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = get_project(project_id, db)
    if project.creator_id != user.id and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the project owner can manage technologies")
    item = ProjectTechnology(project_id=project_id, name=payload.name)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "name": item.name}
