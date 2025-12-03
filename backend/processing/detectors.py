from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path

# Define model paths - using absolute paths as per user environment
SHUTTLECOCK_MODEL_PATH = r"e:\Badminton\frontend\files\shuttlecock\best.pt"
COURT_MODEL_PATH = r"e:\Badminton\frontend\files\line\best.pt"

class ShuttlecockDetector:
    def __init__(self, model_path=SHUTTLECOCK_MODEL_PATH):
        self.model = YOLO(model_path)

    def detect(self, frame):
        """
        Detects shuttlecock in the frame.
        Returns a list of bounding boxes [x1, y1, x2, y2, conf, cls].
        """
        results = self.model(frame, verbose=False)
        detections = []
        for result in results:
            boxes = result.boxes.cpu().numpy()
            for box in boxes:
                detections.append(np.concatenate((box.xyxy[0], [box.conf[0]], [box.cls[0]])))
        return detections

class CourtDetector:
    def __init__(self, model_path=COURT_MODEL_PATH):
        self.model = YOLO(model_path)

    def detect(self, frame):
        """
        Detects court lines/area in the frame.
        Returns a list of bounding boxes or masks depending on the model type.
        Assuming the model detects the 'court' as a bounding box or polygon.
        """
        results = self.model(frame, verbose=False)
        detections = []
        for result in results:
            boxes = result.boxes.cpu().numpy()
            for box in boxes:
                detections.append(np.concatenate((box.xyxy[0], [box.conf[0]], [box.cls[0]])))
        return detections
