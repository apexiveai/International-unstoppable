from __future__ import annotations

from app.services.document_extractors.base import ExtractedDocument

from app.services.document_extractors.pdf_extractor import (

    extract_pdf,

)

from app.services.document_extractors.docx_extractor import (

    extract_docx,

)

from app.services.document_extractors.pptx_extractor import (

    extract_pptx,

)

from app.services.document_extractors.xlsx_extractor import (

    extract_xlsx,

)

from app.services.document_extractors.image_extractor import (

    extract_image,

)

def extract_document(

    filename: str,

    mime_type: str,

    file_bytes: bytes,

) -> ExtractedDocument:

    filename_lower = filename.lower()

    # PDF

    if (

        mime_type == "application/pdf"

        or filename_lower.endswith(".pdf")

    ):

        return extract_pdf(

            filename,

            mime_type,

            file_bytes,

        )

    # DOCX

    if (

        mime_type

        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        or filename_lower.endswith(".docx")

    ):

        return extract_docx(

            filename,

            mime_type,

            file_bytes,

        )

    # PPTX

    if (

        mime_type

        == "application/vnd.openxmlformats-officedocument.presentationml.presentation"

        or filename_lower.endswith(".pptx")

    ):

        return extract_pptx(

            filename,

            mime_type,

            file_bytes,

        )

    # XLSX

    if (

        mime_type

        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        or filename_lower.endswith(".xlsx")

    ):

        return extract_xlsx(

            filename,

            mime_type,

            file_bytes,

        )

    # Images

    if (

        mime_type.startswith("image/")

        or filename_lower.endswith(

            (

                ".jpg",

                ".jpeg",

                ".png",

                ".webp",

            )

        )

    ):

        return extract_image(

            filename,

            mime_type,

            file_bytes,

        )

    raise ValueError(

        f"Unsupported document type: {filename}"

    )