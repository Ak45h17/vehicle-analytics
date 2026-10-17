
import cv2
from pathlib import Path

MODEL_DIR = Path("..") / "Secondary_CarColor"

PROTOTXT = MODEL_DIR / "resnet18.prototxt"
WEIGHTS = MODEL_DIR / "resnet18.caffemodel"
LABELS = MODEL_DIR / "labels.txt"

def main():
    labels = LABELS.read_text(encoding="utf-8").strip().split(";")
    net = cv2.dnn.readNetFromCaffe(str(PROTOTXT), str(WEIGHTS))

    # Confirm the expected input shape: 224 x 224 RGB.
    test_image = 255 * __import__("numpy").ones(
        (224, 224, 3), dtype="uint8"
    )

    blob = cv2.dnn.blobFromImage(
        test_image,
        scalefactor=1.0,
        size=(224, 224),
        mean=(0, 0, 0),
        swapRB=True,
        crop=False,
    )

    net.setInput(blob)

    try:
        output = net.forward()
        print("Output shape:", output.shape)
        print("Number of labels:", len(labels))
        print("Model inference succeeded.")
        print("Note: a white test image is not a meaningful vehicle prediction.")
    except cv2.error as error:
        print("Inference failed:")
        print(error)

if __name__ == "__main__":
    main()
