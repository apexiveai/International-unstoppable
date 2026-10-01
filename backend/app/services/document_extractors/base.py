from __future__ import annotations

from dataclasses import dataclass, field

@dataclass

class DocumentSection:

    type: str

    identifier: str

    text: str = ""

    metadata: dict = field(default_factory=dict)

@dataclass

class ExtractedDocument:

    filename: str

    file_type: str

    mime_type: str

    size_bytes: int

    text: str = ""

    pages: int = 0

    slides: int = 0

    sheets: int = 0

    metadata: dict = field(default_factory=dict)

    images: list[dict] = field(default_factory=list)

    structure: list[dict] = field(default_factory=list)

    sections: list[DocumentSection] = field(

        default_factory=list

    )