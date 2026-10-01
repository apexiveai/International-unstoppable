from typing import Dict, List, Tuple

import cv2

import numpy as np

from app.services.clone_detector.image_utils import (

    image_to_base64,

    load_document_images,

)

from app.services.clone_detector.models import (

    MatchArea,

)

MAX_MATCHES_PER_PAIR = 500

TOP_MATCH_AREAS = 3

def _prepare_gray(

    image: np.ndarray,

) -> np.ndarray:

    return cv2.cvtColor(

        image,

        cv2.COLOR_BGR2GRAY,

    )

def _create_detector():

    return cv2.ORB_create(

        nfeatures=5000,

        scaleFactor=1.2,

        nlevels=8,

        edgeThreshold=31,

        firstLevel=0,

        WTA_K=2,

        scoreType=cv2.ORB_HARRIS_SCORE,

        patchSize=31,

        fastThreshold=20,

    )

def _detect_features(

    image: np.ndarray,

):

    gray = _prepare_gray(image)

    detector = _create_detector()

    keypoints, descriptors = detector.detectAndCompute(

        gray,

        None,

    )

    return keypoints, descriptors

def _match_features(

    original_descriptors,

    comparison_descriptors,

):

    if (

        original_descriptors is None

        or comparison_descriptors is None

    ):

        return []

    if (

        len(original_descriptors) < 2

        or len(comparison_descriptors) < 2

    ):

        return []

    matcher = cv2.BFMatcher(

        cv2.NORM_HAMMING,

        crossCheck=False,

    )

    raw_matches = matcher.knnMatch(

        original_descriptors,

        comparison_descriptors,

        k=2,

    )

    good_matches = []

    for pair in raw_matches:

        if len(pair) != 2:

            continue

        first, second = pair

        if first.distance < 0.72 * second.distance:

            good_matches.append(first)

    good_matches.sort(

        key=lambda match: match.distance

    )

    return good_matches[

        :MAX_MATCHES_PER_PAIR

    ]

def _cluster_points(

    points: List[Tuple[float, float]],

):

    """

    Spatial clustering using DBSCAN.

    Returns clusters as lists of point indexes.

    """

    if len(points) < 3:

        return []

    data = np.array(

        points,

        dtype=np.float32,

    )

    if len(data) < 3:

        return []

    labels = np.full(

        len(data),

        -1,

        dtype=np.int32,

    )

    cluster_id = 0

    radius = 90.0

    min_points = 3

    for index in range(len(data)):

        if labels[index] != -1:

            continue

        distances = np.linalg.norm(

            data - data[index],

            axis=1,

        )

        neighbours = np.where(

            distances <= radius

        )[0]

        if len(neighbours) < min_points:

            continue

        labels[index] = cluster_id

        queue = list(

            neighbours

        )

        while queue:

            current = queue.pop()

            if labels[current] == -1:

                labels[current] = cluster_id

                current_distances = np.linalg.norm(

                    data - data[current],

                    axis=1,

                )

                current_neighbours = np.where(

                    current_distances <= radius

                )[0]

                if len(current_neighbours) >= min_points:

                    queue.extend(

                        current_neighbours.tolist()

                    )

        cluster_id += 1

    clusters = []

    for cid in range(cluster_id):

        indexes = np.where(

            labels == cid

        )[0].tolist()

        if indexes:

            clusters.append(indexes)

    return clusters

def _build_match_area(

    points: List[Tuple[float, float]],

    indexes: List[int],

    image_shape,

    match_id: int,

) -> MatchArea:

    cluster_points = np.array(

        [

            points[index]

            for index in indexes

        ],

        dtype=np.float32,

    )

    x_values = cluster_points[:, 0]

    y_values = cluster_points[:, 1]

    min_x = float(np.min(x_values))

    max_x = float(np.max(x_values))

    min_y = float(np.min(y_values))

    max_y = float(np.max(y_values))

    padding = 60

    x = max(

        0,

        int(min_x - padding),

    )

    y = max(

        0,

        int(min_y - padding),

    )

    right = min(

        image_shape[1],

        int(max_x + padding),

    )

    bottom = min(

        image_shape[0],

        int(max_y + padding),

    )

    width = max(

        50,

        right - x,

    )

    height = max(

        50,

        bottom - y,

    )

    center_x = int(

        x + width / 2

    )

    center_y = int(

        y + height / 2

    )

    radius = max(

        35,

        int(

            max(width, height) / 2

        ),

    )

    return MatchArea(

        match_id=match_id,

        page=1,

        score=min(

            0.99,

            0.55

            + (

                len(indexes)

                / 100

            ),

        ),

        x=x,

        y=y,

        width=width,

        height=height,

        center_x=center_x,

        center_y=center_y,

        radius=radius,

        matched_points=len(indexes),

    )

def _find_areas(

    original: np.ndarray,

    comparison: np.ndarray,

):

    original_keypoints, original_descriptors = (

        _detect_features(original)

    )

    comparison_keypoints, comparison_descriptors = (

        _detect_features(comparison)

    )

    matches = _match_features(

        original_descriptors,

        comparison_descriptors,

    )

    if not matches:

        return []

    original_points = []

    for match in matches:

        point = original_keypoints[

            match.queryIdx

        ].pt

        original_points.append(

            point

        )

    clusters = _cluster_points(

        original_points

    )

    areas = []

    for cluster_index, indexes in enumerate(

        clusters[:TOP_MATCH_AREAS],

        start=1,

    ):

        area = _build_match_area(

            original_points,

            indexes,

            original.shape,

            cluster_index,

        )

        areas.append(area)

    areas.sort(

        key=lambda item: (

            item.matched_points,

            item.score,

        ),

        reverse=True,

    )

    for index, area in enumerate(

        areas[:TOP_MATCH_AREAS],

        start=1,

    ):

        area.match_id = index

    return areas[:TOP_MATCH_AREAS]

def analyze_clone(

    original_filename: str,

    original_mime_type: str,

    original_bytes: bytes,

    comparison_filename: str,

    comparison_mime_type: str,

    comparison_bytes: bytes,

) -> Dict:

    """

    Complete clone analysis.

    Returns:

        - similarity

        - top 3 matching areas

        - annotated original pages

        - comparison pages

    """

    original_pages = load_document_images(

        original_filename,

        original_mime_type,

        original_bytes,

    )

    comparison_pages = load_document_images(

        comparison_filename,

        comparison_mime_type,

        comparison_bytes,

    )

    if not original_pages:

        raise ValueError(

            "Original document contains no readable pages."

        )

    if not comparison_pages:

        raise ValueError(

            "Comparison document contains no readable pages."

        )

    all_results = []

    annotated_pages = []

    total_score = 0.0

    total_matches = 0

    page_count = min(

        len(original_pages),

        len(comparison_pages),

    )

    for page_index in range(page_count):

        original_image = original_pages[

            page_index

        ]

        comparison_image = comparison_pages[

            page_index

        ]

        areas = _find_areas(

            original_image,

            comparison_image,

        )

        for area in areas:

            area.page = page_index + 1

        all_results.extend(

            areas

        )

    all_results.sort(

        key=lambda item: (

            item.matched_points,

            item.score,

        ),

        reverse=True,

    )

    all_results = all_results[
:TOP_MATCH_AREAS

    ]

    for area in all_results:

        total_score += area.score

        total_matches += area.matched_points

    if all_results:

        overall_similarity = (

            total_score

            / len(all_results)

        )

    else:

        overall_similarity = 0.0

    by_page = {}

    for area in all_results:

        by_page.setdefault(

            area.page,

            [],

        ).append(area)

    for page_index, original_image in enumerate(

        original_pages,

        start=1,

    ):

        annotated = original_image.copy()

        page_areas = by_page.get(

            page_index,

            [],

        )

        for area in page_areas:

            annotated = (

                __import__(

                    "app.services.clone_detector.image_utils",

                    fromlist=[

                        "draw_match_area"

                    ],

                ).draw_match_area(

                    annotated,

                    area.x,

                    area.y,

                    area.width,

                    area.height,

                    area.match_id,

                )

            )

        annotated_pages.append(

            {

                "page": page_index,

                "image": image_to_base64(

                    annotated

                ),

            }

        )

    return {

        "overall_similarity": round(

            overall_similarity,

            4,

        ),

        "similarity_percent": round(

            overall_similarity * 100,

            2,

        ),

        "matching_area_count": len(

            all_results

        ),

        "matched_points": total_matches,

        "matches": [

            {

                "match_id": area.match_id,

                "page": area.page,

                "score": round(

                    area.score,

                    4,

                ),

                "score_percent": round(

                    area.score * 100,

                    2,

                ),

                "x": area.x,

                "y": area.y,

                "width": area.width,

                "height": area.height,

                "center_x": area.center_x,

                "center_y": area.center_y,

                "radius": area.radius,

                "matched_points": area.matched_points,

            }

            for area in all_results

        ],

        "annotated_original": annotated_pages,

        "original_page_count": len(

            original_pages

        ),

        "comparison_page_count": len(

            comparison_pages

        ),

        "engine": {

            "name": "Apexive Visual Clone Engine",

            "version": "1.0.0",

            "method": "ORB + BFMatcher + spatial clustering",

        },

    }