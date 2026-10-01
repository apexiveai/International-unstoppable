import base64

import io

from typing import List, Tuple

import pymupdf

import numpy as np

from PIL import Image

SUPPORTED_IMAGE_TYPES = {

    "image/jpeg",

    "image/png",

    "image/webp",

}

SUPPORTED_PDF_TYPE = "application/pdf"

def image_to_base64(image: np.ndarray) -> str:

    """

    Convert OpenCV BGR image into data URL.

    """

    rgb = image[:, :, ::-1]

    pil_image = Image.fromarray(rgb)

    buffer = io.BytesIO()

    pil_image.save(

        buffer,

        format="JPEG",

        quality=88,

        optimize=True,

    )

    encoded = base64.b64encode(

        buffer.getvalue()

    ).decode("utf-8")

    return f"data:image/jpeg;base64,{encoded}"

def bytes_to_image(

    file_bytes: bytes,

) -> np.ndarray:

    """

    Convert image bytes into OpenCV BGR image.

    """

    image = Image.open(

        io.BytesIO(file_bytes)

    )

    image = image.convert("RGB")

    array = np.asarray(image)

    return array[:, :, ::-1].copy()

def pdf_to_images(

    file_bytes: bytes,

    max_pages: int = 20,

    dpi: int = 120,

) -> List[np.ndarray]:

    """

    Render PDF pages into OpenCV BGR images.

    """

    document = pymupdf.open(

        stream=file_bytes,

        filetype="pdf",

    )

    images: List[np.ndarray] = []

    page_count = min(

        len(document),

        max_pages,

    )

    scale = dpi / 72.0

    matrix = pymupdf.Matrix(

        scale,

        scale,

    )

    try:

        for page_index in range(page_count):

            page = document.load_page(

                page_index

            )

            pixmap = page.get_pixmap(

                matrix=matrix,

                alpha=False,

            )

            image = np.frombuffer(

                pixmap.samples,

                dtype=np.uint8,

            )

            image = image.reshape(

                pixmap.height,

                pixmap.width,

                pixmap.n,

            )

            if pixmap.n == 4:

                image = image[:, :, :3]

            image = image[:, :, ::-1].copy()

            images.append(image)

    finally:

        document.close()

    return images

def load_document_images(

    filename: str,

    mime_type: str,

    file_bytes: bytes,

) -> List[np.ndarray]:

    """

    Load PDF or image into one or more OpenCV images.

    """

    filename_lower = (

        filename.lower()

    )

    if (

        mime_type == SUPPORTED_PDF_TYPE

        or filename_lower.endswith(".pdf")

    ):

        return pdf_to_images(

            file_bytes

        )

    if (

        mime_type in SUPPORTED_IMAGE_TYPES

        or filename_lower.endswith(

            (".jpg", ".jpeg", ".png", ".webp")

        )

    ):

        return [

            bytes_to_image(file_bytes)

        ]

    raise ValueError(

        "Unsupported file type. "

        "Supported formats: PDF, JPG, PNG, WEBP."

    )

def draw_match_area(

    image: np.ndarray,

    x: int,

    y: int,

    width: int,

    height: int,

    match_id: int,

) -> np.ndarray:

    """

    Draw a green ellipse around a detected matching area.

    """

    import cv2

    output = image.copy()

    center = (

        int(x + width / 2),

        int(y + height / 2),

    )

    axes = (

        max(int(width / 2), 25),

        max(int(height / 2), 25),

    )

    cv2.ellipse(

        output,

        center,

        axes,

        0,

        0,

        360,

        (0, 255, 0),

        5,

        cv2.LINE_AA,

    )

    label = f"CLONE AREA {match_id}"

    label_x = max(

        10,

        int(x),

    )

    label_y = max(

        30,

        int(y) - 10,

    )

    cv2.putText(

        output,

        label,

        (

            label_x,

            label_y,

        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.8,

        (0, 255, 0),

        2,

        cv2.LINE_AA,

    )

    return output