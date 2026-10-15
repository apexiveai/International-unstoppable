from __future__ import annotations

import httpx

from app.core.config import settings


class SpaceshipError(Exception):
    pass


class SpaceshipNotConfiguredError(SpaceshipError):
    pass


class SpaceshipTimeoutError(SpaceshipError):
    pass


async def check_domain_availability(domain: str) -> dict[str, str]:
    if not settings.spaceship_api_key or not settings.spaceship_api_secret:
        raise SpaceshipNotConfiguredError(
            "Spaceship API credentials are not configured."
        )

    url = f"{settings.spaceship_api_base_url.rstrip('/')}/domains/available"
    headers = {
        "X-Api-Key": settings.spaceship_api_key,
        "X-Api-Secret": settings.spaceship_api_secret,
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10, connect=5)) as client:
            response = await client.post(
                url,
                headers=headers,
                json={"domains": [domain]},
            )
    except httpx.TimeoutException as exc:
        raise SpaceshipTimeoutError(
            "Spaceship domain availability lookup timed out."
        ) from exc
    except httpx.RequestError as exc:
        raise SpaceshipError(
            "Unable to connect to Spaceship domain availability service."
        ) from exc

    if response.status_code in {401, 403}:
        raise SpaceshipError(
            "Spaceship rejected the API credentials or their permissions."
        )
    if not response.is_success:
        raise SpaceshipError(
            f"Spaceship domain lookup failed (HTTP {response.status_code})."
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise SpaceshipError("Spaceship returned an invalid response.") from exc

    entries = payload.get("domains") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        raise SpaceshipError("Spaceship returned an unexpected availability response.")

    entry = next(
        (
            item
            for item in entries
            if isinstance(item, dict)
            and isinstance(item.get("domain"), str)
            and item["domain"].lower() == domain.lower()
        ),
        None,
    )
    if (
        entry is None
        or not isinstance(entry.get("result"), str)
        or entry["result"] not in {"available", "taken", "reserved"}
    ):
        raise SpaceshipError("Spaceship returned an unexpected availability result.")

    return {"domain": domain, "result": entry["result"]}
