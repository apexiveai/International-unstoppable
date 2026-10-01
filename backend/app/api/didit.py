from typing import Any

from fastapi import APIRouter, Request

router = APIRouter(

    prefix="/api/didit",

    tags=["Didit"],

)

@router.post("/callback")

async def didit_callback(request: Request) -> dict[str, Any]:

    """

    Didit webhook/callback endpoint.

    Didit can notify this endpoint when a verification

    session changes state.

    The actual authentication decision is still verified

    through the Didit Decision API in /api/auth/face/complete.

    """

    try:

        payload = await request.json()

    except Exception:

        payload = {}

    print("===== DIDIT CALLBACK =====")

    print("PAYLOAD:", payload)

    print("==========================")

    return {

        "status": "received",

    }