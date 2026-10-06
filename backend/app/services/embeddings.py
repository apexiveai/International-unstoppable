import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException, status

from app.core.config import settings


def embed_text(text: str) -> list[float] | None:
    if not settings.embedding_api_key:
        return None

    request = Request(
        settings.embedding_api_url,
        data=json.dumps(
            {"model": settings.embedding_model, "input": text}
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.embedding_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Embedding provider is unavailable.",
        ) from exc

    data = payload.get("data")
    if not isinstance(data, list) or not data or not isinstance(data[0], dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Embedding provider returned an invalid response.",
        )
    vector = data[0].get("embedding")
    if not isinstance(vector, list) or not all(isinstance(item, (int, float)) for item in vector):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Embedding provider returned an invalid vector.",
        )
    return [float(item) for item in vector]
