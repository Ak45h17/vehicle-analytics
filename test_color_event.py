
import cv2
import requests
from pathlib import Path

MODEL_DIR = Path("..") / "Secondary_CarColor"
labels = (MODEL_DIR / "labels.txt").read_text().strip().split(";")

net = cv2.dnn.readNetFromCaffe(
    str(MODEL_DIR / "resnet18.prototxt"),
    str(MODEL_DIR / "resnet18.caffemodel"),
)

# Use a synthetic image to verify the complete event pipeline.
image = 255 * __import__("numpy").ones(
    (224, 224, 3), dtype="uint8"
)

blob = cv2.dnn.blobFromImage(
    image, 1.0, (224, 224), (0, 0, 0),
    swapRB=True, crop=False
)
net.setInput(blob)
scores = net.forward().reshape(-1)
color = labels[int(scores.argmax())]

response = requests.post(
    "http://localhost:5000/api/events",
    json={
        "vehicle_id": 999,
        "color": color,
        "direction": "Test",
        "source_id": "Color_Classifier_Test",
    },
    timeout=5,
)

print("Predicted test color:", color)
print("API status:", response.status_code)
print("Saved event:", response.json())
