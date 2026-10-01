from pydantic import BaseModel

class CloneMatch(BaseModel):

    match_id: int

    page: int

    score: float

    score_percent: float

    x: int

    y: int

    width: int

    height: int

    center_x: int

    center_y: int

    radius: int

    matched_points: int

class AnnotatedPage(BaseModel):

    page: int

    image: str

class CloneDetectorResponse(BaseModel):

    overall_similarity: float

    similarity_percent: float

    matching_area_count: int

    matched_points: int

    matches: list[CloneMatch]

    annotated_original: list[AnnotatedPage]

    original_page_count: int

    comparison_page_count: int

    engine: dict