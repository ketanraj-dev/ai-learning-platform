"""
app/services/face_service.py
-----------------------------
Face recognition utilities — pure functions, no DB access.

LAZY IMPORT FIX:
    face_recognition is imported ONLY when a function is actually called,
    not at server startup. This prevents the 5+ minute startup freeze
    caused by dlib loading its 100MB model files on import.
"""

import io
from typing import Optional

import numpy as np
from fastapi import HTTPException, status
from PIL import Image

from app.core.logging import get_logger

logger = get_logger(__name__)

# We do NOT import face_recognition here at module level.
# It is imported inside each function that needs it.
# This way the server starts in seconds.
FACE_RECOGNITION_AVAILABLE = None  # None = not checked yet


def _get_face_recognition():
    """
    Lazily import face_recognition only when first needed.
    Returns the module or raises HTTPException if not available.
    
    After first call, result is cached in FACE_RECOGNITION_AVAILABLE.
    """
    global FACE_RECOGNITION_AVAILABLE

    if FACE_RECOGNITION_AVAILABLE is True:
        import face_recognition
        return face_recognition

    if FACE_RECOGNITION_AVAILABLE is False:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Face recognition service not available on this server.",
        )

    # First call — try to import
    try:
        import sys
        import io as _io
        # Suppress the noisy "Please install face_recognition_models" print
        _old_stdout = sys.stdout
        sys.stdout = _io.StringIO()
        import face_recognition
        sys.stdout = _old_stdout
        FACE_RECOGNITION_AVAILABLE = True
        logger.info("face_recognition loaded successfully (lazy import)")
        return face_recognition
    except ImportError:
        FACE_RECOGNITION_AVAILABLE = False
        logger.warning("face_recognition not available — face login disabled.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Face recognition service not available on this server.",
        )


def encode_face(image_bytes: bytes) -> Optional[np.ndarray]:
    """
    Convert raw image bytes into a 128-dimensional face encoding vector.

    Args:
        image_bytes: raw image file bytes from webcam capture

    Returns:
        numpy array of shape (128,) if a face is found
        None if no face detected in the image
    """
    fr = _get_face_recognition()

    try:
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_array = np.array(pil_image)
    except Exception as e:
        logger.error("Failed to decode image: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not decode image. Please send a valid JPEG or PNG.",
        )

    face_locations = fr.face_locations(image_array)

    if not face_locations:
        logger.warning("No face detected in uploaded image")
        return None

    if len(face_locations) > 1:
        logger.warning(
            "Multiple faces detected (%d) — using the first one",
            len(face_locations),
        )

    encodings = fr.face_encodings(image_array, face_locations)

    if not encodings:
        logger.warning("Could not generate encoding from detected face")
        return None

    logger.info("Successfully encoded face (shape=%s)", encodings[0].shape)
    return encodings[0]


def verify_face(
    image_bytes: bytes,
    stored_encodings: list[tuple[str, np.ndarray]],
    tolerance: float = 0.6,
) -> tuple[Optional[str], float]:
    """
    Compare a webcam image against all stored face encodings.

    Returns:
        (user_id, confidence) if match found
        (None, 0.0) if no match or no face in image
    """
    fr = _get_face_recognition()

    if not stored_encodings:
        logger.warning("No stored face encodings to compare against")
        return None, 0.0

    incoming_encoding = encode_face(image_bytes)
    if incoming_encoding is None:
        return None, 0.0

    known_encodings = [enc for _, enc in stored_encodings]
    user_ids = [uid for uid, _ in stored_encodings]

    matches = fr.compare_faces(
        known_encodings,
        incoming_encoding,
        tolerance=tolerance,
    )
    distances = fr.face_distance(known_encodings, incoming_encoding)

    if not any(matches):
        logger.info(
            "No face match found among %d stored encodings",
            len(stored_encodings),
        )
        return None, 0.0

    best_idx = None
    best_distance = float("inf")

    for i, (is_match, distance) in enumerate(zip(matches, distances)):
        if is_match and distance < best_distance:
            best_distance = distance
            best_idx = i

    if best_idx is None:
        return None, 0.0

    matched_user_id = user_ids[best_idx]
    confidence = round(max(0.0, 1.0 - best_distance), 3)

    logger.info(
        "Face match: user_id=%s distance=%.3f confidence=%.1f%%",
        matched_user_id,
        best_distance,
        confidence * 100,
    )
    return matched_user_id, confidence


def is_available() -> bool:
    """
    Check if face recognition is available.
    Does NOT trigger the actual import — just returns current status.
    Returns True only after a successful lazy load.
    """
    return FACE_RECOGNITION_AVAILABLE is True