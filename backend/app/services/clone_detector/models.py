from dataclasses import dataclass

@dataclass

class MatchArea:

    match_id: int

    page: int

    score: float

    x: int

    y: int

    width: int

    height: int

    center_x: int

    center_y: int

    radius: int

    matched_points: int