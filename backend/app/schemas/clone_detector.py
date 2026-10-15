from typing import Literal

from pydantic import BaseModel, Field, field_validator

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


class SpaceshipDomainAvailabilityRequest(BaseModel):
    domain: str = Field(min_length=3, max_length=253)

    @field_validator("domain")
    @classmethod
    def normalize_and_validate_domain(cls, value: str) -> str:
        domain = value.strip().rstrip(".").lower()
        try:
            domain = domain.encode("idna").decode("ascii")
        except UnicodeError as exc:
            raise ValueError("Enter a valid domain name.") from exc

        labels = domain.split(".")
        if (
            len(labels) < 2
            or len(domain) > 253
            or any(
                not label
                or len(label) > 63
                or label.startswith("-")
                or label.endswith("-")
                or not label.replace("-", "").isalnum()
                for label in labels
            )
        ):
            raise ValueError("Enter a valid domain name, such as example.com.")
        return domain


class SpaceshipDomainAvailabilityResponse(BaseModel):
    domain: str
    result: Literal["available", "taken", "reserved"]
