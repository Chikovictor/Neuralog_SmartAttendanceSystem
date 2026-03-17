import os
import sys
from pathlib import Path
from collections import defaultdict

import cv2
import numpy as np
from keras_facenet import metadata as facenet_metadata
from sklearn.metrics import accuracy_score

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from recognition.utils import FaceRecognizerService, extract_faces, get_embedding


def ensure_facenet_weights() -> bool:
    key = os.environ.get("FACENET_MODEL_KEY", "20180402-114759")
    cache_folder = os.environ.get("FACENET_CACHE", "~/.keras-facenet")
    meta = facenet_metadata.MODEL_METADATA.get(key)
    if not meta:
        print(f"Unknown FaceNet model key: {key}")
        return False
    weights_path = os.path.join(
        os.path.expanduser(cache_folder),
        meta["dir_name"],
        meta["keras_weights_filename"],
    )
    if os.path.exists(weights_path):
        return True
    print("FaceNet weights not found; benchmark will not start.")
    print(f"Download: {meta['keras_weights_url']}")
    print(f"Place at: {weights_path}")
    return False


def infer_condition(name: str) -> str:
    name = name.lower()
    for key in ("left", "right", "up", "down", "tilt", "dark", "bright", "low", "high"):
        if key in name:
            return key
    return "normal"


def load_predictions(base_path: str, model_path: str):
    recognizer = FaceRecognizerService(model_path=model_path)
    y_true = []
    y_pred = []
    conditions = defaultdict(list)

    for label in sorted(os.listdir(base_path)):
        label_path = os.path.join(base_path, label)
        if not os.path.isdir(label_path):
            continue
        for img_file in os.listdir(label_path):
            img_path = os.path.join(label_path, img_file)
            img = cv2.imread(img_path, cv2.IMREAD_COLOR)
            if img is None:
                continue
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            faces = extract_faces(img_rgb, max_faces=1)
            if not faces:
                continue
            emb = get_embedding(faces[0]).reshape(1, -1)
            pred = recognizer.svm.predict(emb)[0]

            y_true.append(label)
            y_pred.append(pred)
            conditions[infer_condition(img_file)].append((label, pred))

    return y_true, y_pred, conditions


def main():
    base_path = "dataset/val"
    model_path = "media/svm_model.pkl"

    if not ensure_facenet_weights():
        return

    if not os.path.exists(model_path):
        print("Model not found. Train the model first.")
        return

    y_true, y_pred, conditions = load_predictions(base_path, model_path)
    if not y_true:
        print("No validation images found.")
        return

    overall = accuracy_score(y_true, y_pred)
    print(f"Overall accuracy: {overall:.4f}")
    print("Condition summary:")
    for condition, items in conditions.items():
        c_true = [t for t, _ in items]
        c_pred = [p for _, p in items]
        acc = accuracy_score(c_true, c_pred)
        print(f"  {condition:10s} -> {acc:.4f} ({len(items)} samples)")


if __name__ == "__main__":
    main()
