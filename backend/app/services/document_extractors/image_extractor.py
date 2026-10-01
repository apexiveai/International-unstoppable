from __future__ import annotations

from io import BytesIO

from PIL import Image

from app.services.document_extractors.base import (

    DocumentSection,

    ExtractedDocument,

)

def extract_image(

    content: bytes,

    filename: str,

    mime_type: str,

) -> ExtractedDocument:

    image = Image.open(

        BytesIO(content)

    )

    width, height = image.size

    return ExtractedDocument(

        filename=filename,

        file_type="image",

        mime_type=mime_type,

        size_bytes=len(content),

        metadata={

            "width": width,

            "height": height,

            "format": image.format,

            "mode": image.mode,

        },

        structure=[

            {

                "type": "image",

                "width": width,

                "height": height,

            }

        ],

        sections=[

            DocumentSection(

                type="image",

                identifier="image-1",

                metadata={

                    "width": width,

                    "height": height,

                },

            )

        ],

    )