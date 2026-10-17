
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

BASE = Path("..")
VIDEO = BASE / "traffic_cam_clear_edited_1.mp4"
MODEL_DIR = BASE / "Secondary_CarColor"

LABELS = (MODEL_DIR / "labels.txt").read_text().strip().split(";")

# Load the original Caffe color classifier.
color_net = cv2.dnn.readNetFromCaffe(
    str(MODEL_DIR / "resnet18.prototxt"),
    str(MODEL_DIR / "resnet18.caffemodel"),
)

# Load the small YOLO model for one-frame vehicle detection.
detector = YOLO("yolo11n.pt")

cap = cv2.VideoCapture(str(VIDEO))
try:
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {VIDEO}")

    # Read only one frame; do not process the full video.
    ok, frame = cap.read()
    if not ok:
        raise RuntimeError("Could not read a frame from the video.")

    height, width = frame.shape[:2]
    # Resize for faster detection.
    small = cv2.resize(frame, (640, 360))
    results = detector(small, classes=[2, 3, 5, 7],
                       conf=0.35, verbose=False)

    boxes = results[0].boxes
    if boxes is None or len(boxes) == 0:
        print("No vehicles found in the first frame. Try another frame.")
    else:
        # Use the largest detected vehicle in this frame.
        coords = boxes.xyxy.cpu().numpy()
        areas = (coords[:, 2] - coords[:, 0]) * (
            coords[:, 3] - coords[:, 1]
        )
        x1, y1, x2, y2 = coords[int(np.argmax(areas))].astype(int)

        # Map coordinates from resized image back to original frame.
        x1 = max(0, int(x1 * width / 640))
        x2 = min(width, int(x2 * width / 640))
        y1 = max(0, int(y1 * height / 360))
        y2 = min(height, int(y2 * height / 360))

        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            raise RuntimeError("Detected vehicle crop is empty.")

        blob = cv2.dnn.blobFromImage(
            crop,
            scalefactor=1.0,
            size=(224, 224),
            mean=(0, 0, 0),
            swapRB=True,
            crop=False,
        )
        color_net.setInput(blob)
        scores = color_net.forward().reshape(-1)

        if len(scores) != len(LABELS):
            raise RuntimeError(
                f"Model returned {len(scores)} scores for "
                f"{len(LABELS)} labels."
            )

        index = int(np.argmax(scores))
        print("Predicted color:", LABELS[index])
        print("Top model score:", round(float(scores[index]), 4))
        print("Note: confidence interpretation depends on model output.")

finally:
    cap.release()
