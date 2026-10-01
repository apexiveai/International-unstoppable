from __future__ import annotations

import re

from dataclasses import dataclass

from rapidfuzz import fuzz

from app.services.document_extractors.base import (

    DocumentSection,

    ExtractedDocument,

)

MAX_TEXT_LENGTH = 100_000

MAX_SECTION_MATCHES = 20

@dataclass

class SectionMatch:

    original_identifier: str

    comparison_identifier: str

    original_type: str

    comparison_type: str

    score: float

    original_text: str

    comparison_text: str

def normalize_text(text: str) -> str:

    text = text.lower()

    text = re.sub(

        r"\s+",

        " ",

        text,

    )

    text = re.sub(

        r"[^\w\s]",

        "",

        text,

    )

    return text.strip()

def calculate_text_similarity(

    original_text: str,

    comparison_text: str,

) -> float:

    original = normalize_text(

        original_text[:MAX_TEXT_LENGTH]

    )

    comparison = normalize_text(

        comparison_text[:MAX_TEXT_LENGTH]

    )

    if not original or not comparison:

        return 0.0

    return round(

        float(

            fuzz.token_set_ratio(

                original,

                comparison,

            )

        ),

        2,

    )

def calculate_structure_similarity(

    original: ExtractedDocument,

    comparison: ExtractedDocument,

) -> float:

    original_structure = original.structure

    comparison_structure = comparison.structure

    if not original_structure or not comparison_structure:

        return 0.0

    original_types = [

        str(item.get("type", ""))

        for item in original_structure

    ]

    comparison_types = [

        str(item.get("type", ""))

        for item in comparison_structure

    ]

    type_score = fuzz.ratio(

        " ".join(original_types),

        " ".join(comparison_types),

    )

    original_count = len(original_structure)

    comparison_count = len(comparison_structure)

    count_score = 100.0 - min(

        100.0,

        (

            abs(

                original_count

                - comparison_count

            )

            / max(

                original_count,

                comparison_count,

            )

        )

        * 100,

    )

    return round(

        type_score * 0.6

        + count_score * 0.4,

        2,

    )

def build_section_signature(

    section: DocumentSection,

) -> str:

    text = normalize_text(

        section.text[:5_000]

    )

    return text

def find_section_matches(

    original_sections: list[DocumentSection],

    comparison_sections: list[DocumentSection],

    threshold: float = 70.0,

) -> list[SectionMatch]:

    valid_original = [

        section

        for section in original_sections

        if section.text.strip()

    ]

    valid_comparison = [

        section

        for section in comparison_sections

        if section.text.strip()

    ]

    if not valid_original or not valid_comparison:

        return []

    comparison_signatures = [

        (

            section,

            build_section_signature(section),

        )

        for section in valid_comparison

    ]

    matches: list[SectionMatch] = []

    for original in valid_original:

        original_signature = (

            build_section_signature(original)

        )

        if not original_signature:

            continue

        candidates = []

        for comparison, signature in comparison_signatures:

            if not signature:

                continue

            quick_score = fuzz.ratio(

                original_signature[:500],

                signature[:500],

            )

            candidates.append(

                (

                    quick_score,

                    comparison,

                )

            )

        candidates.sort(

            key=lambda item: item[0],

            reverse=True,

        )

        # Only deeply compare the strongest candidates.

        for _, comparison in candidates[:5]:

            score = calculate_text_similarity(

                original.text,
comparison.text,

            )

            if score >= threshold:

                matches.append(

                    SectionMatch(

                        original_identifier=(

                            original.identifier

                        ),

                        comparison_identifier=(

                            comparison.identifier

                        ),

                        original_type=original.type,

                        comparison_type=comparison.type,

                        score=score,

                        original_text=(

                            original.text[:500]

                        ),

                        comparison_text=(

                            comparison.text[:500]

                        ),

                    )

                )

                break

    matches.sort(

        key=lambda item: item.score,

        reverse=True,

    )

    return matches[:MAX_SECTION_MATCHES]

def compare_documents(

    original: ExtractedDocument,

    comparison: ExtractedDocument,

) -> dict:

    text_similarity = calculate_text_similarity(

        original.text,

        comparison.text,

    )

    structure_similarity = (

        calculate_structure_similarity(

            original,

            comparison,

        )

    )

    section_matches = find_section_matches(

        original.sections,

        comparison.sections,

    )

    if section_matches:

        section_average = (

            sum(

                match.score

                for match in section_matches

            )

            / len(section_matches)

        )

    else:

        section_average = 0.0

        overall_similarity = round(

            text_similarity * 0.55

            + structure_similarity * 0.25

            + section_average * 0.20,

            2,

        )

    return {

        "overall_similarity": overall_similarity,

        "text_similarity": round(

            text_similarity,

            2,

        ),

        "structure_similarity": round(

            structure_similarity,

            2,

        ),

        "section_similarity": round(

            section_average,

            2,

        ),

        "matching_sections": [

            {

                "original_identifier": (

                    match.original_identifier

                ),

                "comparison_identifier": (

                    match.comparison_identifier

                ),

                "original_type": (

                    match.original_type

                ),

                "comparison_type": (

                    match.comparison_type

                ),

                "score": match.score,

                "original_text": (

                    match.original_text

                ),

                "comparison_text": (

                    match.comparison_text

                ),

            }

            for match in section_matches

        ],

    }