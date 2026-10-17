
from pathlib import Path

import cv2
import requests
from ultralytics import YOLO


# --------------------------------------------------
# Configuration
# --------------------------------------------------

VIDEO_PATH = Path("..") / "traffic_cam_clear_edited_1.mp4"
API_URL = "http://localhost:5000/api/events"

SOURCE_ID = "Traffic_Camera_1"

# COCO classes: car, motorcycle, bus, truck
VEHICLE_CLASSES = [2, 3, 5, 7]

LINE_Y_RATIO = 0.60

# CPU optimization
PROCESS_EVERY_N_FRAMES = 2
DISPLAY_WIDTH = 960

# YOLO model
YOLO_MODEL_PATH = "yolo11n.pt"

# Original Caffe vehicle color classifier
MODEL_DIR = Path("..") / "Secondary_CarColor"

PROTOTXT_PATH = MODEL_DIR / "resnet18.prototxt"
WEIGHTS_PATH = MODEL_DIR / "resnet18.caffemodel"
LABELS_PATH = MODEL_DIR / "labels.txt"

COLOR_LABELS = (
    LABELS_PATH.read_text(encoding="utf-8").strip().split(";")
)

VEHICLE_NAMES = {
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck",
}


# --------------------------------------------------
# Load the color classifier
# --------------------------------------------------

color_net = cv2.dnn.readNetFromCaffe(
    str(PROTOTXT_PATH),
    str(WEIGHTS_PATH),
)

# Explicitly use CPU for the color model.
color_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
color_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)


# --------------------------------------------------
# Vehicle color classification
# --------------------------------------------------

def classify_vehicle_color(frame, box):
    """
    Classify a vehicle crop using the original Caffe model.

    The preprocessing matches the initial CPU test.
    Predictions should be validated against real examples.
    """
    x1, y1, x2, y2 = map(int, box)

    height, width = frame.shape[:2]

    x1 = max(0, min(x1, width - 1))
    x2 = max(0, min(x2, width))
    y1 = max(0, min(y1, height - 1))
    y2 = max(0, min(y2, height))

    crop = frame[y1:y2, x1:x2]

    if crop.size == 0:
        return "Unknown"

    blob = cv2.dnn.blobFromImage(
        crop,
        scalefactor=1.0,
        size=(224, 224),
        mean=(0, 0, 0),
        swapRB=True,
        crop=False,
    )

    try:
        color_net.setInput(blob)
        scores = color_net.forward().reshape(-1)

        if len(scores) != len(COLOR_LABELS):
            return "Unknown"

        return COLOR_LABELS[int(scores.argmax())]

    except cv2.error as error:
        print(f"Color classification failed: {error}")
        return "Unknown"


# --------------------------------------------------
# Main detection and tracking pipeline
# --------------------------------------------------

def main():
    print("Loading YOLO model...")
    detector = YOLO(YOLO_MODEL_PATH)

    print(f"Opening video: {VIDEO_PATH}")
    cap = cv2.VideoCapture(str(VIDEO_PATH))

    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {VIDEO_PATH}")

    previous_positions = {}
    counted_ids = set()
    frame_number = 0

    try:
        while True:
            success, original_frame = cap.read()

            if not success:
                print("Video ended.")
                break

            frame_number += 1

            original_height, original_width = original_frame.shape[:2]

            # Resize while preserving the original aspect ratio.
            scale = min(1.0, DISPLAY_WIDTH / original_width)

            if scale < 1.0:
                frame = cv2.resize(
                    original_frame,
                    (
                        int(original_width * scale),
                        int(original_height * scale),
                    ),
                    interpolation=cv2.INTER_AREA,
                )
            else:
                frame = original_frame

            height, width = frame.shape[:2]
            line_y = int(height * LINE_Y_RATIO)

            # Process only alternate frames to reduce CPU work.
            # Skipped frames may reduce tracking accuracy.
            if frame_number % PROCESS_EVERY_N_FRAMES != 0:
                continue

            results = detector.track(
                frame,
                persist=True,
                tracker="bytetrack.yaml",
                classes=VEHICLE_CLASSES,
                conf=0.35,
                imgsz=640,
                device="cpu",
                verbose=False,
            )

            result = results[0]
            annotated = result.plot()

            cv2.line(
                annotated,
                (0, line_y),
                (width, line_y),
                (0, 255, 255),
                2,
            )

            cv2.putText(
                annotated,
                f"Events counted: {len(counted_ids)}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )

            boxes_obj = result.boxes

            if (
                boxes_obj is not None
                and boxes_obj.id is not None
            ):
                boxes = boxes_obj.xyxy.cpu().tolist()
                track_ids = boxes_obj.id.int().cpu().tolist()
                classes = boxes_obj.cls.int().cpu().tolist()

                for box, track_id, class_id in zip(
                    boxes, track_ids, classes
                ):
                    x1, y1, x2, y2 = map(int, box)
                    center_y = (y1 + y2) // 2

                    previous_y = previous_positions.get(track_id)
                    previous_positions[track_id] = center_y

                    if previous_y is None:
                        continue

                    crossed = (
                        (previous_y < line_y <= center_y)
                        or (previous_y > line_y >= center_y)
                    )

                    if not crossed or track_id in counted_ids:
                        continue

                    # Count each tracker ID once per script run.
                    counted_ids.add(track_id)

                    vehicle_name = VEHICLE_NAMES.get(
                        class_id, "Unknown"
                    )

                    # Classify color only when a crossing occurs.
                    vehicle_color = classify_vehicle_color(
                        frame, box
                    )

                    direction = (
                        "Down" if center_y > previous_y else "Up"
                    )

                    # Tracker IDs may be reused after a restart.
                    # This is not a globally unique event ID.
                    vehicle_id = int(track_id)

                    print(
                        f"Crossing: track={track_id}, "
                        f"type={vehicle_name}, "
                        f"color={vehicle_color}, "
                        f"direction={direction}"
                    )

                    try:
                        response = requests.post(
                            API_URL,
                            json={
                                "vehicle_id": vehicle_id,
                                "vehicle_type": vehicle_name,
                                "color": vehicle_color,
                                "direction": direction,
                                "source_id": SOURCE_ID,
                            },
                            timeout=3,
                        )

                        response.raise_for_status()

                        print(
                            f"Saved event successfully: "
                            f"HTTP {response.status_code}"
                        )

                    except requests.RequestException as error:
                        print(
                            f"Could not save event: {error}"
                        )

            cv2.imshow(
                "CPU Vehicle Analytics",
                annotated,
            )

            # Press Q to stop the detector.
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("Stopped by user.")
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
