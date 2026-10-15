import json

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
)
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.auth import get_current_user
from app.database import get_db
from app.models import TrademarkConflictCheck, User
from app.schemas.clone_detector import (
    CloneDetectorResponse,
)
from app.services.clone_detector import (
    analyze_clone,
)
from app.services.product_access import require_tenant_product_access
from app.services.audit_service import write_audit_log

router = APIRouter(

    prefix="/api/clone-detector",

    tags=["Clone Detector"],

)

MAX_FILE_SIZE = 20 * 1024 * 1024
HISTORY_PAGE_SIZE = 10

ALLOWED_EXTENSIONS = {

    ".pdf",

    ".jpg",

    ".jpeg",

    ".png",

    ".webp",

}

def validate_file(

    filename: str | None,

):

    if not filename:

        raise HTTPException(

            status_code=400,

            detail="File name is required.",

        )

    filename_lower = filename.lower()

    if not any(

        filename_lower.endswith(extension)

        for extension in ALLOWED_EXTENSIONS

    ):

        raise HTTPException(

            status_code=415,

            detail=(

                "Unsupported file type. "

                "Supported: PDF, JPG, JPEG, PNG, WEBP."

            ),

        )

def validate_file_signature(filename: str, content: bytes) -> None:
    extension = filename.lower().rsplit(".", 1)[-1]
    valid = {
        "pdf": content.startswith(b"%PDF-"),
        "jpg": content.startswith(b"\xff\xd8\xff"),
        "jpeg": content.startswith(b"\xff\xd8\xff"),
        "png": content.startswith(b"\x89PNG\r\n\x1a\n"),
        "webp": (
            len(content) >= 12
            and content[:4] == b"RIFF"
            and content[8:12] == b"WEBP"
        ),
    }
    if not valid.get(extension, False):
        raise HTTPException(
            status_code=400,
            detail=f"The uploaded {extension.upper()} file has an invalid file signature.",
        )

@router.post(
    "/analyze",
    response_model=CloneDetectorResponse,
)
async def analyze_clone_documents(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.tenant_id is None:
        raise HTTPException(
            status_code=403,
            detail="User is not assigned to a tenant.",
        )
    require_tenant_product_access(db, user.tenant_id, "trademark")

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > 2 * MAX_FILE_SIZE + 64 * 1024:
                raise HTTPException(
                    status_code=413,
                    detail="Upload request exceeds the allowed size.",
                )
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid content length.",
            ) from exc
    try:
        form = await request.form(max_files=2, max_fields=0, max_part_size=MAX_FILE_SIZE)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid multipart upload.",
        ) from exc
    original_files = form.getlist("original")
    comparison_files = form.getlist("comparison")
    if (
        len(original_files) != 1
        or len(comparison_files) != 1
        or not isinstance(original_files[0], StarletteUploadFile)
        or not isinstance(comparison_files[0], StarletteUploadFile)
    ):
        raise HTTPException(
            status_code=422,
            detail="Exactly one original file and one comparison file are required.",
        )
    original = original_files[0]
    comparison = comparison_files[0]
    try:
        validate_file(original.filename)
        validate_file(comparison.filename)
        original_bytes = await original.read(MAX_FILE_SIZE + 1)
        comparison_bytes = await comparison.read(MAX_FILE_SIZE + 1)
    finally:
        await form.close()

    if len(original_bytes) > MAX_FILE_SIZE:

        raise HTTPException(

            status_code=413,

            detail="Original file is too large. Maximum size is 20 MB.",

        )

    if len(comparison_bytes) > MAX_FILE_SIZE:

        raise HTTPException(

            status_code=413,

            detail="Comparison file is too large. Maximum size is 20 MB.",

        )

    if not original_bytes:

        raise HTTPException(

            status_code=400,

            detail="Original file is empty.",

        )

    if not comparison_bytes:

        raise HTTPException(

            status_code=400,

            detail="Comparison file is empty.",
        )
    validate_file_signature(original.filename or "", original_bytes)
    validate_file_signature(comparison.filename or "", comparison_bytes)

    try:
        result = analyze_clone(

            original_filename=(

                original.filename

                or "original"

            ),

            original_mime_type=(

                original.content_type

                or ""

            ),

            original_bytes=original_bytes,

            comparison_filename=(

                comparison.filename

                or "comparison"

            ),

            comparison_mime_type=(

                comparison.content_type

                or ""

            ),

            comparison_bytes=comparison_bytes,

        )

    except ValueError as exc:

        raise HTTPException(

            status_code=422,

            detail=str(exc),

        ) from exc
    except Exception as exc:
        print(
            "[CloneDetector] Analysis failed:",
            repr(exc),
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Clone detection failed. "
                "Please verify that both files are readable."
            ),
        ) from exc

    check = TrademarkConflictCheck(
        tenant_id=user.tenant_id,
        user_id=user.id,
        original_filename=(original.filename or "original")[:255],
        comparison_filename=(comparison.filename or "comparison")[:255],
        result_payload=json.dumps(result.model_dump(mode="json")),
    )
    db.add(check)
    db.flush()
    write_audit_log(
        db,
        tenant_id=user.tenant_id,
        actor_user_id=user.id,
        action="trademark_conflict.check_created",
        target_type="trademark_conflict_check",
        target_id=check.id,
        new_value={
            "original_filename": check.original_filename,
            "comparison_filename": check.comparison_filename,
            "similarity_percent": result.similarity_percent,
        },
    )
    db.commit()
    return result


@router.get("/checks")
def list_trademark_checks(
    page: int = Query(default=1, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.tenant_id is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a tenant.")
    require_tenant_product_access(db, user.tenant_id, "trademark")
    total = db.scalar(
        select(func.count(TrademarkConflictCheck.id)).where(
            TrademarkConflictCheck.tenant_id == user.tenant_id
        )
    ) or 0
    checks = db.scalars(
        select(TrademarkConflictCheck)
        .where(TrademarkConflictCheck.tenant_id == user.tenant_id)
        .order_by(desc(TrademarkConflictCheck.created_at), desc(TrademarkConflictCheck.id))
        .offset((page - 1) * HISTORY_PAGE_SIZE)
        .limit(HISTORY_PAGE_SIZE)
    ).all()
    return {
        "items": [
            {
                "id": check.id,
                "original_filename": check.original_filename,
                "comparison_filename": check.comparison_filename,
                "similarity_percent": json.loads(check.result_payload)[
                    "similarity_percent"
                ],
                "created_at": check.created_at,
            }
            for check in checks
        ],
        "total": total,
        "page": page,
        "page_size": HISTORY_PAGE_SIZE,
        "pages": min(100, (total + HISTORY_PAGE_SIZE - 1) // HISTORY_PAGE_SIZE),
    }


@router.get("/checks/{check_id}")
def get_trademark_check(
    check_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.tenant_id is None:
        raise HTTPException(status_code=403, detail="User is not assigned to a tenant.")
    require_tenant_product_access(db, user.tenant_id, "trademark")
    check = db.scalar(
        select(TrademarkConflictCheck).where(
            TrademarkConflictCheck.id == check_id,
            TrademarkConflictCheck.tenant_id == user.tenant_id,
        )
    )
    if check is None:
        raise HTTPException(status_code=404, detail="Trademark Conflict check not found.")
    return {
        "id": check.id,
        "original_filename": check.original_filename,
        "comparison_filename": check.comparison_filename,
        "similarity_percent": json.loads(check.result_payload)[
            "similarity_percent"
        ],
        "created_at": check.created_at,
        "result": json.loads(check.result_payload),
    }