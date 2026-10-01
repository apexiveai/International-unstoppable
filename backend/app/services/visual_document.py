from __future__ import annotations

import io

import math

from dataclasses import dataclass

import cv2

import pymupdf

import numpy as np

from PIL import Image

MAX_RENDER_PAGES = 20

MAX_RENDER_WIDTH = 1600

MIN_MATCH_COUNT = 8

@dataclass

class RenderedPage:

    index: int

    image: np.ndarray

@dataclass

class VisualDocumentResult:

    similarity: float

    matching_keypoints: int

    matches: list[dict]

    pages_original: int

    pages_comparison: int

def resize_for_analysis(image: np.ndarray) -> np.ndarray:

    height, width = image.shape[:2]

    if width <= MAX_RENDER_WIDTH:

        return image

    scale = MAX_RENDER_WIDTH / width

    new_width = int(width * scale)

    new_height = int(height * scale)

    return cv2.resize(

        image,

        (new_width, new_height),

        interpolation=cv2.INTER_AREA,

    )

def render_pdf_pages(pdf_bytes: bytes) -> list[RenderedPage]:

    document = pymupdf.open(

        stream=pdf_bytes,

        filetype="pdf",

    )

    pages: list[RenderedPage] = []

    try:

        page_count = min(

            len(document),

            MAX_RENDER_PAGES,

        )

        for index in range(page_count):

            page = document.load_page(index)

            matrix = pymupdf.Matrix(

                1.5,

                1.5,

            )

            pixmap = page.get_pixmap(

                matrix=matrix,

                alpha=False,

            )

            image_bytes = pixmap.tobytes(

                "png"

            )

            image = Image.open(

                io.BytesIO(image_bytes)

            ).convert("RGB")

            image_array = np.array(image)

            image_array = cv2.cvtColor(

                image_array,

                cv2.COLOR_RGB2BGR,

            )

            image_array = resize_for_analysis(

                image_array

            )

            pages.append(

                RenderedPage(

                    index=index,

                    image=image_array,

                )

            )

    finally:

        document.close()

    return pages

def image_from_bytes(image_bytes: bytes) -> np.ndarray:

    image = Image.open(

        io.BytesIO(image_bytes)

    ).convert("RGB")

    image_array = np.array(image)

    return cv2.cvtColor(

        image_array,

        cv2.COLOR_RGB2BGR,

    )

def extract_features(

    image: np.ndarray,

):

    gray = cv2.cvtColor(

        image,

        cv2.COLOR_BGR2GRAY,

    )

    gray = cv2.GaussianBlur(

        gray,

        (3, 3),

        0,

    )

    sift = cv2.SIFT_create(

        nfeatures=3000,

    )

    keypoints, descriptors = sift.detectAndCompute(

        gray,

        None,

    )

    return keypoints, descriptors

def compare_images(

    original: np.ndarray,

    comparison: np.ndarray,

):

    original = resize_for_analysis(original)

    comparison = resize_for_analysis(comparison)

    original_keypoints, original_descriptors = extract_features(

        original

    )

    comparison_keypoints, comparison_descriptors = extract_features(

        comparison

    )

    if (

        original_descriptors is None

        or comparison_descriptors is None

    ):

        return 0.0, 0, []

    if (

        len(original_keypoints) < MIN_MATCH_COUNT

        or len(comparison_keypoints) < MIN_MATCH_COUNT

    ):

        return 0.0, 0, []

    matcher = cv2.BFMatcher(

        cv2.NORM_L2,

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

    if len(good_matches) < MIN_MATCH_COUNT:

        return 0.0, len(good_matches), []

    original_points = np.float32(

        [

            original_keypoints[m.queryIdx].pt

            for m in good_matches

        ]

    )

    comparison_points = np.float32(

        [
comparison_keypoints[m.trainIdx].pt

            for m in good_matches

        ]

    )

    if len(original_points) < 4:

        return 0.0, len(good_matches), []

    homography, mask = cv2.findHomography(

        original_points,

        comparison_points,

        cv2.RANSAC,

        5.0,

    )

    if mask is None:

        return 0.0, len(good_matches), []

    inlier_mask = mask.ravel().astype(bool)

    inlier_count = int(

        np.sum(inlier_mask)

    )

    if inlier_count == 0:

        return 0.0, len(good_matches), []

    inlier_ratio = (

        inlier_count

        / max(len(good_matches), 1)

    )

    match_strength = min(

        1.0,

        inlier_count / 100.0,

    )

    similarity = (

        inlier_ratio * 0.6

        + match_strength * 0.4

    ) * 100.0

    similarity = min(

        100.0,

        max(0.0, similarity),

    )

    matches = []

    original_height, original_width = original.shape[:2]

    comparison_height, comparison_width = comparison.shape[:2]

    for index, match in enumerate(good_matches):

        if not inlier_mask[index]:

            continue

        ox, oy = original_keypoints[

            match.queryIdx

        ].pt

        cx, cy = comparison_keypoints[

            match.trainIdx

        ].pt

        matches.append(

            {

                "id": index,

                "score": round(

                    max(

                        0.0,

                        100.0

                        - match.distance,

                    ),

                    2,

                ),

                "original": {

                    "x": round(

                        ox / original_width * 100,

                        2,

                    ),

                    "y": round(

                        oy / original_height * 100,

                        2,

                    ),

                    "width": 2.0,

                    "height": 2.0,

                },

                "comparison": {

                    "x": round(

                        cx / comparison_width * 100,

                        2,

                    ),

                    "y": round(

                        cy / comparison_height * 100,

                        2,

                    ),

                    "width": 2.0,

                    "height": 2.0,

                },

            }

        )

        if len(matches) >= 50:

            break

    return (

        round(similarity, 2),

        inlier_count,

        matches,

    )

def compare_pdf_documents(

    original_bytes: bytes,

    comparison_bytes: bytes,

) -> VisualDocumentResult:

    original_pages = render_pdf_pages(

        original_bytes

    )

    comparison_pages = render_pdf_pages(

        comparison_bytes

    )

    if not original_pages or not comparison_pages:

        return VisualDocumentResult(

            similarity=0.0,

            matching_keypoints=0,

            matches=[],

            pages_original=len(original_pages),

            pages_comparison=len(comparison_pages),

        )

    page_results = []

    for original_page in original_pages:

        best_score = 0.0

        best_keypoints = 0

        best_matches = []

        for comparison_page in comparison_pages:

            score, keypoints, matches = compare_images(

                original_page.image,

                comparison_page.image,

            )

            if score > best_score:

                best_score = score

                best_keypoints = keypoints

                best_matches = matches

        page_results.append(

            (

                best_score,

                best_keypoints,

                best_matches,

                original_page.index,

            )

        )

    page_results.sort(

        key=lambda item: item[0],

        reverse=True,

    )

    significant_results = [

        result

        for result in page_results

        if result[0] >= 5.0

    ]

    if not significant_results:
        return VisualDocumentResult(

            similarity=0.0,

            matching_keypoints=0,

            matches=[],

            pages_original=len(original_pages),

            pages_comparison=len(comparison_pages),

        )

    top_results = significant_results[:10]

    similarity = sum(

        result[0]

        for result in top_results

    ) / len(top_results)

    matching_keypoints = max(

        result[1]

        for result in top_results

    )

    matches = top_results[0][2]

    return VisualDocumentResult(

        similarity=round(

            similarity,

            2,

        ),

        matching_keypoints=matching_keypoints,

        matches=matches,

        pages_original=len(original_pages),

        pages_comparison=len(comparison_pages),

    )