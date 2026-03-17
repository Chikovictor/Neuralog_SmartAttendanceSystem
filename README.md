# Smart Attendance (NeuraLog)

This project is a Django-based smart attendance system that uses MTCNN for face detection and FaceNet for embeddings. It supports staff roles (admin/lecturer/manager), unit-based attendance, and webcam liveness checks.

## Requirements

- Python 3.10+
- Django 4.2
- opencv-python
- opencv-contrib-python
- mtcnn
- keras-facenet (TensorFlow backend)
- mediapipe (for blink detection)
- scikit-learn
- pillow
- pandas / openpyxl (report export)

Optional:
- MySQL (production database)

## Setup

1. Create and activate a virtual environment.
2. Install dependencies.
3. Run migrations (first time or after model changes):

```
python manage.py makemigrations accounts students
python manage.py migrate
```

4. Create an admin user:

```
python manage.py createsuperuser
```

5. Run the server:

```
python manage.py runserver
```

## Dataset Structure (Training Script)

The training script expects the dataset to be organized as:

```
dataset/
  train/
    student001/
      1.pgm
      2.pgm
  val/
    student001/
      10.pgm
```

Folder names should match student identifiers used in your dataset (only for training/testing).

## Training the Model

The training script:
- Detects faces with MTCNN.
- Generates FaceNet embeddings.
- Trains a linear SVM classifier.
- Prints validation accuracy and classification report.
- Saves the model to `media/svm_model.pkl`.

Run:

```
python recognition/train.py
```

## Liveness Detection

Webcam attendance uses a simple blink detector based on Eye Aspect Ratio (EAR) with MediaPipe FaceMesh. If blink detection fails, attendance is rejected.

## Staff + Unit Setup

1. Create units in the Django admin and assign lecturers.
2. (Optional) Set lecturer departments so managers can filter by department.
3. Register students and assign them to units.

## Attendance Flow

1. Lecturer opens a unit.
2. Clicks **Take Attendance** to open the webcam page.
3. The system captures multiple frames, checks for a blink, recognizes the face against students enrolled in the unit, and marks attendance once per day.

## Benchmark Script

To approximate the paper's angle/lighting tests, run:

```
python recognition/test_benchmark.py
```

This script prints accuracy per condition based on filename tags like `left`, `right`, `dark`, etc. If your validation set is organized by conditions, rename files accordingly to get more accurate breakdowns.

## Notes

- For best accuracy, ensure clear and front-facing images during registration.
- Face matching uses direct embedding comparison (Euclidean distance). Tune the threshold in `neuralog/settings.py` (`FACE_MATCH_THRESHOLD`).
- You can switch the database engine in `neuralog/settings.py` to use MySQL.
