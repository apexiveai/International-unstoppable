from __future__ import annotations
from app.services.semantic_similarity import (
    SemanticSimilarityEngine,
)
import cv2

import numpy as np

MAX_IMAGE_BYTES = 20 * 1024 * 1024

MAX_IMAGE_DIMENSION = 3000

MIN_GOOD_MATCHES = 8

MIN_INLIER_MATCHES = 6

class CloneDetectionError(Exception):

    pass

def decode_image(image_bytes: bytes) -> np.ndarray:

    if not image_bytes:

        raise CloneDetectionError("Empty image file.")

    if len(image_bytes) > MAX_IMAGE_BYTES:

        raise CloneDetectionError("Image exceeds the 20MB limit.")

    buffer = np.frombuffer(image_bytes, dtype=np.uint8)

    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)

    if image is None:

        raise CloneDetectionError(

            "Invalid or unsupported image file."

        )

    height, width = image.shape[:2]

    if height < 32 or width < 32:

        raise CloneDetectionError(

            "Image is too small. Minimum size is 32x32 pixels."

        )

    return image

def resize_for_analysis(image: np.ndarray) -> np.ndarray:

    height, width = image.shape[:2]

    longest_side = max(height, width)

    if longest_side <= MAX_IMAGE_DIMENSION:

        return image

    scale = MAX_IMAGE_DIMENSION / longest_side

    new_width = max(1, int(width * scale))

    new_height = max(1, int(height * scale))

    return cv2.resize(

        image,

        (new_width, new_height),

        interpolation=cv2.INTER_AREA,

    )

def create_detector():

    return cv2.SIFT_create(

        nfeatures=8000,

        contrastThreshold=0.04,

        edgeThreshold=10,

        sigma=1.6,

    )

def calculate_similarity(

    good_matches: list[cv2.DMatch],

    total_keypoints: int,

) -> float:

    if not good_matches or total_keypoints <= 0:

        return 0.0

    match_ratio = len(good_matches) / total_keypoints

    score = min(match_ratio * 100.0, 100.0)

    return round(score, 1)

def region_from_points(

    points: np.ndarray,

    image_width: int,

    image_height: int,

):

    if len(points) < 4:

        return None

    x, y, width, height = cv2.boundingRect(

        points.astype(np.float32)

    )

    width = max(width, 1)

    height = max(height, 1)

    return {

        "x": round((x / image_width) * 100, 2),

        "y": round((y / image_height) * 100, 2),

        "width": round((width / image_width) * 100, 2),

        "height": round((height / image_height) * 100, 2),

    }

def calculate_match_region(

    keypoints_original,

    keypoints_comparison,

    matches: list[cv2.DMatch],

    original_shape,

    comparison_shape,

):

    if len(matches) < MIN_INLIER_MATCHES:

        return None

    original_points = np.float32(

        [

            keypoints_original[m.queryIdx].pt

            for m in matches

        ]

    ).reshape(-1, 1, 2)

    comparison_points = np.float32(

        [

            keypoints_comparison[m.trainIdx].pt

            for m in matches

        ]

    ).reshape(-1, 1, 2)

    matrix, mask = cv2.findHomography(

        original_points,

        comparison_points,

        cv2.RANSAC,

        5.0,

    )

    if matrix is None or mask is None:

        return None

    inlier_mask = mask.ravel().astype(bool)

    inlier_count = int(inlier_mask.sum())

    if inlier_count < MIN_INLIER_MATCHES:

        return None

    inlier_original = original_points[inlier_mask]

    inlier_comparison = comparison_points[inlier_mask]

    original_height, original_width = original_shape[:2]

    comparison_height, comparison_width = comparison_shape[:2]

    original_region = region_from_points(

        inlier_original,

        original_width,

        original_height,

    )

    comparison_region = region_from_points(

        inlier_comparison,

        comparison_width,

        comparison_height,

    )

    if not original_region or not comparison_region:

        return None

    score = round(

        min(

            (inlier_count / max(len(matches), 1)) * 100,

            100,

        ),

        1,

    )

    return {

        "score": score,

        "original": original_region,

        "comparison": comparison_region,
        
        "inlier_count": inlier_count,

    }

def cluster_matches(

    keypoints_original,

    keypoints_comparison,

    good_matches: list[cv2.DMatch],

):

    """

    Divide matching feature points into spatial groups.

    This lets us detect multiple copied regions instead of

    returning only one large region.

    """

    if len(good_matches) < MIN_GOOD_MATCHES:

        return []

    original_points = np.float32(

        [

            keypoints_original[m.queryIdx].pt

            for m in good_matches

        ]

    )

    if len(original_points) < MIN_GOOD_MATCHES:

        return []

    # Normalize points to 0-100 coordinate space.

    min_x = original_points[:, 0].min()

    max_x = original_points[:, 0].max()

    min_y = original_points[:, 1].min()

    max_y = original_points[:, 1].max()

    width = max(max_x - min_x, 1.0)

    height = max(max_y - min_y, 1.0)

    normalized = np.column_stack(

        [

            ((original_points[:, 0] - min_x) / width) * 100,

            ((original_points[:, 1] - min_y) / height) * 100,

        ]

    ).astype(np.float32)

    # Spatial clustering.

    criteria = (

        cv2.TERM_CRITERIA_EPS

        + cv2.TERM_CRITERIA_MAX_ITER,

        50,

        1.5,

    )

    max_clusters = min(8, max(1, len(good_matches) // 8))

    compactness, labels, centers = cv2.kmeans(

        normalized,

        max_clusters,

        None,

        criteria,

        10,

        cv2.KMEANS_PP_CENTERS,

    )

    groups = []

    for cluster_id in range(max_clusters):

        cluster_matches = [

            match

            for index, match in enumerate(good_matches)

            if labels[index][0] == cluster_id

        ]

        if len(cluster_matches) < MIN_INLIER_MATCHES:

            continue

        groups.append(cluster_matches)

    return groups

def build_regions(

    keypoints_original,

    keypoints_comparison,

    good_matches,

    original_shape,

    comparison_shape,

):

    groups = cluster_matches(

        keypoints_original,

        keypoints_comparison,

        good_matches,

    )

    regions = []

    for group in groups:

        region = calculate_match_region(

            keypoints_original,

            keypoints_comparison,

            group,

            original_shape,

            comparison_shape,

        )

        if region is None:

            continue

        regions.append(region)

    # Highest-confidence areas first.

    regions.sort(

        key=lambda item: item["score"],

        reverse=True,

    )

    # Limit UI to strongest regions.

    regions = regions[:10]

    formatted = []

    for index, region in enumerate(regions, start=1):

        formatted.append(

            {

                "id": index,

                "score": region["score"],

                "original": region["original"],

                "comparison": region["comparison"],

            }

        )

    return formatted

def analyze_images(

    original_bytes: bytes,

    comparison_bytes: bytes,

):

    original = decode_image(original_bytes)

    comparison = decode_image(comparison_bytes)

    original = resize_for_analysis(original)

    comparison = resize_for_analysis(comparison)

    original_gray = cv2.cvtColor(

        original,

        cv2.COLOR_BGR2GRAY,

    )

    comparison_gray = cv2.cvtColor(

        comparison,

        cv2.COLOR_BGR2GRAY,

    )

    detector = create_detector()

    keypoints_original, descriptors_original = (

        detector.detectAndCompute(

            original_gray,

            None,

        )

    )

    keypoints_comparison, descriptors_comparison = (

        detector.detectAndCompute(

            comparison_gray,

            None,

        )

    )

    if (

        descriptors_original is None

        or descriptors_comparison is None

    ):

        return {

            "similarity_score": 0.0,

            "matching_keypoints": 0,

            "matches": [],

            "status": "no_features_detected",

        }

    matcher = cv2.BFMatcher(
        cv2.NORM_L2,

        crossCheck=False,

    )

    raw_matches = matcher.knnMatch(

        descriptors_original,

        descriptors_comparison,

        k=2,

    )

    good_matches: list[cv2.DMatch] = []

    for pair in raw_matches:

        if len(pair) < 2:

            continue

        first, second = pair

        if first.distance < 0.72 * second.distance:

            good_matches.append(first)

    total_keypoints = max(

        len(keypoints_original),

        len(keypoints_comparison),

    )

    similarity_score = calculate_similarity(

        good_matches,

        total_keypoints,

    )

    regions = build_regions(

        keypoints_original,

        keypoints_comparison,

        good_matches,

        original.shape,

        comparison.shape,

    )

    semantic_engine = SemanticSimilarityEngine()

    semantic_result = semantic_engine.analyze(
        original_bytes,
        comparison_bytes,
    )

    if regions:

        status = "matches_detected"

    elif good_matches:

        status = "weak_similarity"

    else:

        status = "no_significant_similarity"

    return {

        "similarity_score": similarity_score,
        "visual_similarity": similarity_score,
        "semantic_similarity": semantic_result.score,
        "matching_keypoints": len(good_matches),

        "matches": regions,

        "status": (

            "matches_detected"

            if regions

            else "no_significant_similarity"

        )
    }