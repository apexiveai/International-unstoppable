from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
import json

from app.models import Project, ProjectEmbedding, ProjectTechnology
from app.schemas.search import ProjectSearchResult
from app.services.embeddings import embed_text
from app.services.project_search import rank_projects

router = APIRouter(prefix="/api/search", tags=["Search"])


def parse_embedding(value: str) -> list[float] | None:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, list) or not all(
        isinstance(item, (int, float)) for item in parsed
    ):
        return None
    return [float(item) for item in parsed]


@router.get("/projects", response_model=list[ProjectSearchResult])
def search_projects(
    q: str = Query(default="", max_length=200),
    technology: str | None = Query(default=None, max_length=100),
    category: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
):
    projects = db.scalars(select(Project)).all()
    technology_rows = db.scalars(select(ProjectTechnology)).all()
    technologies: dict[int, list[str]] = {}
    for row in technology_rows:
        technologies.setdefault(row.project_id, []).append(row.name)
    embedding_rows = db.scalars(select(ProjectEmbedding)).all()
    embeddings = {
        row.project_id: parsed
        for row in embedding_rows
        if (parsed := parse_embedding(row.vector)) is not None
    }
    query_embedding = embed_text(q) if q.strip() else None
    return rank_projects(
        projects,
        technologies,
        q,
        technology,
        category,
        query_embedding,
        embeddings,
    )
