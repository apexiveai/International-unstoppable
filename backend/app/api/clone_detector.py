from fastapi import (

    APIRouter,

    File,

    HTTPException,

    UploadFile,

)

from app.schemas.clone_detector import (

    CloneDetectorResponse,

)

from app.services.clone_detector import (

    analyze_clone,

)

router = APIRouter(

    prefix="/api/clone-detector",

    tags=["Clone Detector"],

)

MAX_FILE_SIZE = 20 * 1024 * 1024

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

@router.post(

    "/analyze",

    response_model=CloneDetectorResponse,

)

async def analyze_clone_documents(

    original: UploadFile = File(...),

    comparison: UploadFile = File(...),

):

    validate_file(

        original.filename

    )

    validate_file(

        comparison.filename

    )

    original_bytes = await original.read()

    comparison_bytes = await comparison.read()

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

        return result

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