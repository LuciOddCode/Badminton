import cv2
from pathlib import Path
from .detectors import ShuttlecockDetector, CourtDetector
from .decision import DecisionEngine
from .utils import draw_detections, draw_decision

class ProcessingEngine:
    def __init__(self):
        self.shuttlecock_detector = ShuttlecockDetector()
        self.court_detector = CourtDetector()
        self.decision_engine = DecisionEngine()

    def process_video(self, video_path, output_path=None):
        """
        Processes the video, runs detection, and generates an output video with visualizations.
        Returns a summary of results.
        """
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

        frame_count = 0
        results_summary = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # 1. Detect
            shuttlecock_dets = self.shuttlecock_detector.detect(frame)
            court_dets = self.court_detector.detect(frame)
            
            # 2. Decide
            decision = self.decision_engine.evaluate(shuttlecock_dets, court_dets)
            
            # 3. Visualize
            frame = draw_detections(frame, shuttlecock_dets, color=(0, 255, 255), label_prefix="Shuttle")
            frame = draw_detections(frame, court_dets, color=(0, 255, 0), label_prefix="Court")
            if decision:
                frame = draw_decision(frame, decision)
                results_summary.append({"frame": frame_count, "decision": decision})

            if output_path:
                out.write(frame)

        cap.release()
        if output_path:
            out.release()

        return results_summary
