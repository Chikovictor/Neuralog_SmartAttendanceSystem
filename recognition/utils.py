import base64
import os
import pickle
from typing import List, Optional, Tuple

import cv2
import numpy as np
from keras_facenet import FaceNet
from mtcnn import MTCNN

UNKNOWN_LABEL = "unknown"

_detector = None
_embedder = None


def get_detector() -> MTCNN:
    global _detector
    if _detector is None:
        _detector = MTCNN()
    return _detector


def get_embedder() -> FaceNet:
    global _embedder
    if _embedder is None:
        _embedder = FaceNet()
    return _embedder


def _expand_box(x: int, y: int, w: int, h: int, scale: float, img_w: int, img_h: int) -> Tuple[int, int, int, int]:
    cx, cy = x + w / 2, y + h / 2
    nw, nh = w * scale, h * scale
    nx = int(max(0, cx - nw / 2))
    ny = int(max(0, cy - nh / 2))
    nw = int(min(img_w - nx, nw))
    nh = int(min(img_h - ny, nh))
    return nx, ny, nw, nh


def extract_faces(image: np.ndarray, scale: float = 1.2, max_faces: Optional[int] = None) -> List[np.ndarray]:
    """Detect faces and return list of 160x160 RGB face crops."""
    detector = get_detector()
    results = detector.detect_faces(image)
    if not results:
        return []

    faces = []
    img_h, img_w = image.shape[:2]
    results = sorted(results, key=lambda r: r["box"][2] * r["box"][3], reverse=True)
    for idx, result in enumerate(results):
        if max_faces and idx >= max_faces:
            break
        x, y, w, h = result["box"]
        x, y = max(0, x), max(0, y)
        x, y, w, h = _expand_box(x, y, w, h, scale, img_w, img_h)
        face = image[y : y + h, x : x + w]
        if face.size == 0:
            continue
        face = cv2.resize(face, (160, 160))
        faces.append(face)
    return faces


def select_best_face_from_frames(frames: List[np.ndarray], scale: float = 1.2) -> Tuple[Optional[np.ndarray], int]:
    """Pick the most confident face crop across multiple frames."""
    detector = get_detector()
    best_face = None
    best_score = 0.0
    best_face_count = 0

    for frame in frames:
        results = detector.detect_faces(frame)
        if not results:
            continue
        if len(results) > best_face_count:
            best_face_count = len(results)
        img_h, img_w = frame.shape[:2]
        for result in results:
            score = float(result.get("confidence", 0.0))
            if score <= best_score:
                continue
            x, y, w, h = result["box"]
            x, y = max(0, x), max(0, y)
            x, y, w, h = _expand_box(x, y, w, h, scale, img_w, img_h)
            face = frame[y : y + h, x : x + w]
            if face.size == 0:
                continue
            face = cv2.resize(face, (160, 160))
            best_face = face
            best_score = score
    return best_face, best_face_count


def get_embedding(face_img: np.ndarray) -> np.ndarray:
    """Convert face image to embedding."""
    embedder = get_embedder()
    face = np.expand_dims(face_img, axis=0)
    return embedder.embeddings(face)[0]


def image_from_bytes(data: bytes) -> Optional[np.ndarray]:
    img_array = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if img is None:
        return None
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def resize_for_speed(image: np.ndarray, max_size: int = 800) -> np.ndarray:
    height, width = image.shape[:2]
    scale = max(height, width) / max_size
    if scale <= 1:
        return image
    new_w = int(width / scale)
    new_h = int(height / scale)
    return cv2.resize(image, (new_w, new_h))


def image_from_base64(data_url: str) -> Optional[np.ndarray]:
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]
    try:
        decoded = base64.b64decode(data_url)
    except (ValueError, TypeError):
        return None
    return image_from_bytes(decoded)


def detect_blink_from_frames(
    frames: List[np.ndarray],
    ear_threshold: float = 0.23,
    min_consecutive: int = 2,
    min_blinks: int = 1,
) -> Optional[bool]:
    """Detect a blink based on Eye Aspect Ratio using MediaPipe."""
    try:
        import mediapipe as mp
        mp_face = mp.solutions.face_mesh
    except Exception:
        return None

    left_eye = [33, 160, 158, 133, 153, 144]
    right_eye = [362, 385, 387, 263, 373, 380]

    def ear(landmarks, eye_idx):
        p1 = landmarks[eye_idx[0]]
        p2 = landmarks[eye_idx[1]]
        p3 = landmarks[eye_idx[2]]
        p4 = landmarks[eye_idx[3]]
        p5 = landmarks[eye_idx[4]]
        p6 = landmarks[eye_idx[5]]
        v1 = np.linalg.norm([p2.x - p6.x, p2.y - p6.y])
        v2 = np.linalg.norm([p3.x - p5.x, p3.y - p5.y])
        h = np.linalg.norm([p1.x - p4.x, p1.y - p4.y])
        if h == 0:
            return 0.0
        return (v1 + v2) / (2.0 * h)

    blink_count = 0
    closed_frames = 0

    with mp_face.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True) as face_mesh:
        for frame in frames:
            results = face_mesh.process(frame)
            if not results.multi_face_landmarks:
                continue
            landmarks = results.multi_face_landmarks[0].landmark
            left = ear(landmarks, left_eye)
            right = ear(landmarks, right_eye)
            avg_ear = (left + right) / 2.0

            if avg_ear < ear_threshold:
                closed_frames += 1
            else:
                if closed_frames >= min_consecutive:
                    blink_count += 1
                closed_frames = 0
            if blink_count >= min_blinks:
                return True
    return False


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    denom = (np.linalg.norm(vec_a) * np.linalg.norm(vec_b)) + 1e-8
    if denom == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / denom)


def euclidean_distance(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    return float(np.linalg.norm(vec_a - vec_b))


def match_student_embedding(embedding: np.ndarray, students, threshold: float = 0.6):
    """Return best matching student and confidence using Euclidean distance."""
    best_student = None
    best_distance = float("inf")

    for student in students:
        for enc in student.face_encodings or []:
            try:
                enc_vec = np.array(enc, dtype=np.float32)
            except (TypeError, ValueError):
                continue
            if enc_vec.shape != embedding.shape:
                continue
            distance = euclidean_distance(embedding, enc_vec)
            if distance < best_distance:
                best_distance = distance
                best_student = student

    if best_student is None:
        return None, 0.0, None

    confidence = max(0.0, 1 - (best_distance / 2))
    if best_distance <= threshold:
        return best_student, confidence, best_distance
    return None, confidence, best_distance


class FaceRecognizerService:
    def __init__(self, model_path: Optional[str] = None):
        self.svm = None
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)

    def load_model(self, model_path: str) -> None:
        with open(model_path, "rb") as f:
            self.svm = pickle.load(f)

    def train_svm(self, X: np.ndarray, y: np.ndarray, save_path: str) -> None:
        from sklearn.svm import SVC

        self.svm = SVC(kernel="linear", probability=True)
        self.svm.fit(X, y)
        with open(save_path, "wb") as f:
            pickle.dump(self.svm, f)

    def predict(self, image: np.ndarray, threshold: float = 0.6) -> Tuple[Optional[str], Optional[float]]:
        faces = extract_faces(image, max_faces=1)
        if not faces:
            return None, None
        emb = get_embedding(faces[0]).reshape(1, -1)
        if self.svm is None:
            return None, None
        probs = self.svm.predict_proba(emb)[0]
        max_prob = float(np.max(probs))
        if max_prob >= threshold:
            label = str(self.svm.classes_[int(np.argmax(probs))])
            return label, max_prob
        return None, None

    def predict_many(self, image: np.ndarray, threshold: float = 0.6) -> List[Tuple[str, float]]:
        faces = extract_faces(image)
        results = []
        for face in faces:
            emb = get_embedding(face).reshape(1, -1)
            if self.svm is None:
                results.append((UNKNOWN_LABEL, 0.0))
                continue
            probs = self.svm.predict_proba(emb)[0]
            max_prob = float(np.max(probs))
            if max_prob >= threshold:
                label = str(self.svm.classes_[int(np.argmax(probs))])
                results.append((label, max_prob))
            else:
                results.append((UNKNOWN_LABEL, max_prob))
        return results
