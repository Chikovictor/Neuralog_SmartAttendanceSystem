import os
import sys
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import cv2
import numpy as np
from keras_facenet import metadata as facenet_metadata
from sklearn.metrics import accuracy_score, classification_report

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
    print("FaceNet weights not found; training will not start.")
    print(f"Download: {meta['keras_weights_url']}")
    print(f"Place at: {weights_path}")
    print("Then rerun: python recognition/train.py")
    return False


def augment_face(face: np.ndarray) -> List[np.ndarray]:
    variants = [face]
    h, w = face.shape[:2]
    center = (w / 2, h / 2)
    for angle in (-10, 10):
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(face, matrix, (w, h))
        variants.append(rotated)
    return variants


def load_dataset(base_path: str, augment: bool = False) -> Tuple[np.ndarray, np.ndarray]:
    X = []
    y = []
    skipped = 0

    for label in sorted(os.listdir(base_path)):
        label_path = os.path.join(base_path, label)
        if not os.path.isdir(label_path):
            continue
        for img_file in os.listdir(label_path):
            img_path = os.path.join(label_path, img_file)
            img = cv2.imread(img_path, cv2.IMREAD_COLOR)
            if img is None:
                skipped += 1
                continue
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            faces = extract_faces(img_rgb, max_faces=1)
            if not faces:
                skipped += 1
                continue
            face = faces[0]
            variants = augment_face(face) if augment else [face]
            for variant in variants:
                emb = get_embedding(variant)
                X.append(emb)
                y.append(label)

    if skipped:
        print(f"Skipped {skipped} images with no face or read error.")
    return np.array(X), np.array(y)


def main():
    train_path = "dataset/train"
    val_path = "dataset/val"
    model_path = "media/svm_model.pkl"
    os.makedirs("media", exist_ok=True)

    if not ensure_facenet_weights():
        return

    print("Loading training data...")
    X_train, y_train = load_dataset(train_path, augment=True)
    print(f"Training samples: {len(X_train)}")

    print("Loading validation data...")
    X_val, y_val = load_dataset(val_path, augment=False)
    print(f"Validation samples: {len(X_val)}")

    fr = FaceRecognizerService()
    fr.train_svm(X_train, y_train, save_path=model_path)

    if len(X_val) > 0:
        preds = fr.svm.predict(X_val)
        acc = accuracy_score(y_val, preds)
        print(f"Validation accuracy: {acc:.4f}")
        print("Classification report:")
        print(classification_report(y_val, preds))
    else:
        print("No validation data found.")

    print(f"Training complete. Model saved to {model_path}.")


if __name__ == "__main__":
    main()
