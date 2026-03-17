from typing import List, Optional, Tuple

import numpy as np

from recognition.liveness import detect_blink_from_frames
from recognition.utils import (
    get_embedding,
    image_from_base64,
    match_student_embedding,
    resize_for_speed,
    select_best_face_from_frames,
)


def decode_frames(payload) -> List[np.ndarray]:
    frames_b64 = payload.get("frames") or []
    if not frames_b64 and payload.get("image"):
        frames_b64 = [payload["image"]]

    frames = []
    for frame_data in frames_b64:
        frame = image_from_base64(frame_data)
        if frame is not None:
            frames.append(resize_for_speed(frame))
    return frames


def run_liveness_check(frames: List[np.ndarray]) -> Tuple[Optional[bool], Optional[str]]:
    try:
        blink_ok = detect_blink_from_frames(frames)
    except Exception:
        blink_ok = None
    if blink_ok is None:
        return None, "MediaPipe not installed; liveness check skipped."
    if not blink_ok:
        return False, None
    return True, None


def recognize_student(embedding: np.ndarray, students, threshold: float):
    student, confidence, distance = match_student_embedding(embedding, students, threshold=threshold)
    confidence_pct = round(confidence * 100, 2)
    return student, confidence_pct, distance


def get_best_face(frames: List[np.ndarray]):
    best_face, face_count = select_best_face_from_frames(frames)
    return best_face, face_count


def create_embedding(face_img: np.ndarray) -> np.ndarray:
    return get_embedding(face_img)
