from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader

from app.services.document_extractors.base import (

    DocumentSection,

    ExtractedDocument,

)

def extract_pdf(

    content: bytes,

    filename: str,

    mime_type: str,

) -> ExtractedDocument:

    reader = PdfReader(BytesIO(content))

    text_parts: list[str] = []

    structure: list[dict] = []

    sections: list[DocumentSection] = []

    for index, page in enumerate(

        reader.pages,

        start=1,

    ):

        try:

            page_text = page.extract_text() or ""

        except Exception:

            page_text = ""

        text_parts.append(page_text)

        structure.append(

            {

                "type": "page",

                "number": index,

                "text_length": len(page_text),

            }

        )

        sections.append(

            DocumentSection(

                type="page",

                identifier=f"page-{index}",

                text=page_text,

                metadata={

                    "page": index,

                },

            )

        )

    metadata = {}

    if reader.metadata:

        for key, value in reader.metadata.items():

            metadata[str(key)] = str(value)

    return ExtractedDocument(

        filename=filename,

        file_type="pdf",

        mime_type=mime_type,

        size_bytes=len(content),

        text="\n".join(text_parts),

        pages=len(reader.pages),

        metadata=metadata,

        structure=structure,

        sections=sections,

    )