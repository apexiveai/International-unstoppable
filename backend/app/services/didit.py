import json

from urllib.error import HTTPError, URLError

from urllib.request import Request, urlopen

from fastapi import HTTPException, status

from app.core.config import settings

def _request(url: str, payload: dict) -> dict:

    request = Request(

        url,

        data=json.dumps(payload).encode("utf-8"),

        headers={

            "Content-Type": "application/json",

            "x-api-key": settings.didit_api_key,

        },

        method="POST",

    )

    try:

        with urlopen(request, timeout=30) as response:

            body = response.read().decode("utf-8")

            print("===== DIDIT CREATE SESSION =====")

            print("STATUS:", response.status)

            print("RESPONSE:", body)

            print("================================")

            return json.loads(body)

    except HTTPError as exc:

        error_body = ""

        try:

            error_body = exc.read().decode("utf-8")

        except Exception:

            pass

        print("===== DIDIT HTTP ERROR =====")

        print("STATUS:", exc.code)

        print("RESPONSE:", error_body)

        print("============================")

        raise HTTPException(

            status_code=status.HTTP_502_BAD_GATEWAY,

            detail={

                "message": "Didit rejected the session request.",

                "didit_status": exc.code,

                "didit_response": error_body,

            },

        ) from exc

    except (URLError, TimeoutError) as exc:

        print("===== DIDIT CONNECTION ERROR =====")

        print(repr(exc))

        print("==================================")

        raise HTTPException(

            status_code=status.HTTP_502_BAD_GATEWAY,

            detail="Cannot connect to Didit.",

        ) from exc

    except json.JSONDecodeError as exc:

        raise HTTPException(

            status_code=status.HTTP_502_BAD_GATEWAY,

            detail="Didit returned invalid JSON.",

        ) from exc

def create_session(email: str, return_to: str) -> dict:

    if not settings.didit_api_key:

        raise HTTPException(

            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,

            detail="DIDIT_API_KEY is not configured.",

        )

    if not settings.didit_workflow_id:

        raise HTTPException(

            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,

            detail="DIDIT_WORKFLOW_ID is not configured.",

        )

    payload = {

        "workflow_id": settings.didit_workflow_id,

        "vendor_data": email,

    }

    if settings.didit_callback_url:

        payload["callback"] = settings.didit_callback_url

    print("===== DIDIT SESSION REQUEST =====")

    print("URL:", settings.didit_api_url)

    print("WORKFLOW:", settings.didit_workflow_id)

    print("VENDOR DATA:", email)

    print("CALLBACK:", settings.didit_callback_url)

    print("=================================")

    result = _request(

        settings.didit_api_url,

        payload,

    )

    session_id = result.get("session_id") or result.get("id")

    verification_url = (

        result.get("url")

        or result.get("session_url")

        or result.get("verification_url")

    )

    if not session_id:

        raise HTTPException(

            status_code=status.HTTP_502_BAD_GATEWAY,

            detail={

                "message": "Didit did not return session_id.",

                "didit_response": result,

            },

        )

    if not verification_url:

        raise HTTPException(

            status_code=status.HTTP_502_BAD_GATEWAY,

            detail={

                "message": "Didit did not return verification URL.",

                "didit_response": result,

            },

        )

    return {

        "session_id": session_id,

        "verification_url": verification_url,

    }

def get_session_status(session_id: str) -> dict:

    if not settings.didit_api_key:

        raise HTTPException(

            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,

            detail="DIDIT_API_KEY is not configured.",
)

    url = settings.didit_status_url.format(

        session_id=session_id

    )

    request = Request(

        url,

        headers={

            "x-api-key": settings.didit_api_key,

        },

        method="GET",

    )

    try:

        with urlopen(request, timeout=30) as response:

            body = response.read().decode("utf-8")

            print("===== DIDIT DECISION =====")

            print("STATUS:", response.status)

            print("RESPONSE:", body)

            print("==========================")

            return json.loads(body)

    except HTTPError as exc:

        error_body = ""

        try:

            error_body = exc.read().decode("utf-8")

        except Exception:

            pass

        print("===== DIDIT DECISION ERROR =====")

        print("STATUS:", exc.code)

        print("RESPONSE:", error_body)

        print("================================")

        raise HTTPException(

            status_code=status.HTTP_502_BAD_GATEWAY,

            detail={

                "message": "Unable to read Didit decision.",

                "didit_status": exc.code,

                "didit_response": error_body,

            },

        ) from exc

    except (URLError, TimeoutError) as exc:

        raise HTTPException(

            status_code=status.HTTP_502_BAD_GATEWAY,

            detail="Cannot connect to Didit.",

        ) from exc

    except json.JSONDecodeError as exc:

        raise HTTPException(

            status_code=status.HTTP_502_BAD_GATEWAY,

            detail="Didit returned invalid decision JSON.",

        ) from exc