import re
import math

from app.models import Project, ProjectTechnology


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return max(0.0, min(1.0, numerator / (left_norm * right_norm)))


def tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9+#.-]+", value.lower())
        if len(token) > 1
    }


def rank_projects(
    projects: list[Project],
    technologies: dict[int, list[str]],
    query: str,
    technology: str | None,
    category: str | None,
    query_embedding: list[float] | None = None,
    embeddings: dict[int, list[float]] | None = None,
) -> list[dict]:
    query_tokens = tokens(query)
    technology_tokens = tokens(technology or "")
    category_value = (category or "").strip().lower()
    ranked = []

    for project in projects:
        project_technologies = technologies.get(project.id, [])
        searchable = tokens(
            " ".join(
                [
                    project.name,
                    project.description,
                    project.content,
                    project.category,
                    " ".join(project_technologies),
                ]
            )
        )
        if technology and not any(
            technology.lower() in item.lower() for item in project_technologies
        ):
            continue
        if category_value and project.category.lower() != category_value:
            continue

        overlap = len(query_tokens & searchable) / max(len(query_tokens), 1)
        title_overlap = len(query_tokens & tokens(project.name)) / max(
            len(query_tokens), 1
        )
        category_match = bool(
            category_value and category_value in project.category.lower()
        )
        lexical_score = min(
            1.0,
            (overlap * 0.6) + (title_overlap * 0.25) + (0.15 if category_match else 0),
        )
        if not query_tokens:
            lexical_score = 0.0
        vector_score = 0.0
        if query_embedding and embeddings and project.id in embeddings:
            vector_score = cosine_similarity(query_embedding, embeddings[project.id])
        score = (vector_score * 0.8) + (lexical_score * 0.2) if query_embedding else lexical_score
        ranked.append(
            {
                "id": project.id,
                "name": project.name,
                "slug": project.slug,
                "description": project.description,
                "category": project.category,
                "status": project.status,
                "technologies": project_technologies,
                "semantic_score": round(score, 4),
                "created_at": project.created_at,
            }
        )

    return sorted(ranked, key=lambda item: (-item["semantic_score"], item["name"].lower()))
