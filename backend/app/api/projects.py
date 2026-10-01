from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import desc, select

from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import settings

from app.database import get_db

import json

from app.models import Project, ProjectEmbedding, ReputationEvent, User
from app.services.embeddings import embed_text

from app.schemas.project import ProjectCreate, ProjectResponse

router = APIRouter(

    prefix="/api/projects",

    tags=["Projects"],

)

@router.get(

    "",

    response_model=list[ProjectResponse],

)

def list_projects(

    db: Session = Depends(get_db),

):

    projects = db.scalars(

        select(Project)

        .order_by(desc(Project.created_at))

    ).all()

    return projects

@router.get(

    "/featured",

    response_model=list[ProjectResponse],

)

def featured_projects(

    db: Session = Depends(get_db),

):

    projects = db.scalars(

        select(Project)

        .where(Project.is_featured.is_(True))

        .order_by(desc(Project.created_at))

    ).all()

    return projects

@router.get(

    "/{slug}",

    response_model=ProjectResponse,

)

def get_project(

    slug: str,

    db: Session = Depends(get_db),

):

    project = db.scalar(

        select(Project).where(

            Project.slug == slug,

        )

    )

    if not project:

        raise HTTPException(

            status_code=status.HTTP_404_NOT_FOUND,

            detail="Project not found",

        )

    project.views += 1

    db.commit()

    db.refresh(project)

    return project


@router.post("/{project_id}/embedding")
def rebuild_project_embedding(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only the project owner can rebuild embeddings")
    vector = embed_text(
        " ".join([project.name, project.description, project.content, project.category])
    )
    if not vector:
        raise HTTPException(
            status_code=503,
            detail="Embedding provider is not configured.",
        )
    embedding = db.scalar(
        select(ProjectEmbedding).where(ProjectEmbedding.project_id == project.id)
    )
    if embedding:
        embedding.model = settings.embedding_model
        embedding.vector = json.dumps(vector)
        embedding.dimensions = len(vector)
    else:
        db.add(ProjectEmbedding(
            project_id=project.id,
            model=settings.embedding_model,
            vector=json.dumps(vector),
            dimensions=len(vector),
        ))
    db.commit()
    return {"project_id": project.id, "model": settings.embedding_model, "dimensions": len(vector)}

@router.post(

    "",

    response_model=ProjectResponse,

    status_code=status.HTTP_201_CREATED,

)

def create_project(

    payload: ProjectCreate,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user),

):

    existing = db.scalar(

        select(Project).where(

            Project.slug == payload.slug,

        )

    )

    if existing:

        raise HTTPException(

            status_code=status.HTTP_409_CONFLICT,

            detail="Project slug already exists",

        )

    is_featured = payload.is_featured if current_user.is_admin else False

    project = Project(
        
        name=payload.name,

        slug=payload.slug,

        description=payload.description,

        content=payload.content,

        category=payload.category,

        creator_id=current_user.id,

        repository_url=payload.repository_url,

        website_url=payload.website_url,

        logo_url=payload.logo_url,

        status=payload.status,

        is_featured=is_featured,

    )

    db.add(project)
    db.flush()
    embedding_text = " ".join(
        [project.name, project.description, project.content, project.category]
    )
    vector = embed_text(embedding_text)
    if vector:
        db.add(ProjectEmbedding(
            project_id=project.id,
            model=settings.embedding_model,
            vector=json.dumps(vector),
            dimensions=len(vector),
        ))
    db.add(ReputationEvent(
        user_id=current_user.id,
        project_id=project.id,
        event_type="project.created",
        points=10,
    ))
    if project.is_featured:
        db.add(ReputationEvent(
            user_id=current_user.id,
            project_id=project.id,
            event_type="project.published",
            points=5,
        ))
    db.commit()

    db.refresh(project)

    return project