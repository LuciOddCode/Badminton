from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path

# Define model paths - using absolute paths as per user environment
SHUTTLECOCK_MODEL_PATH = r"E:\Badminton\backend\best2.pt"
COURT_MODEL_PATH = r"E:\Badminton\backend\bestcourt.pt"

class ShuttlecockDetector:
    def __init__(self, model_path=SHUTTLECOCK_MODEL_PATH):
        self.model = YOLO(model_path)

    def detect(self, frame):
        """
        Detects shuttlecock in the frame.
        Returns a list of bounding boxes [x1, y1, x2, y2, conf, cls].
        """
        # Inference Resizing optimization
        # Resize to 640 width (standard YOLO size) while maintaining aspect ratio
        height, width = frame.shape[:2]
        target_width = 640
        scale = target_width / width
        target_height = int(height * scale)
        
        resized_frame = cv2.resize(frame, (target_width, target_height))
        
        results = self.model(resized_frame, verbose=False)
        detections = []
        for result in results:
            boxes = result.boxes.cpu().numpy()
            for box in boxes:
                # Scale boxes back to original size
                scaled_box = box.xyxy[0] / scale
                detections.append(np.concatenate((scaled_box, [box.conf[0]], [box.cls[0]])))
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
        # Inference Resizing optimization
        height, width = frame.shape[:2]
        target_width = 640
        scale = target_width / width
        target_height = int(height * scale)
        
        resized_frame = cv2.resize(frame, (target_width, target_height))

        results = self.model(resized_frame, verbose=False)
        detections = []
        for result in results:
            boxes = result.boxes.cpu().numpy()
            for box in boxes:
                # Scale boxes back to original size
                scaled_box = box.xyxy[0] / scale
                detections.append(np.concatenate((scaled_box, [box.conf[0]], [box.cls[0]])))
        return detections
