import cv2
from pathlib import Path
from .detectors import ShuttlecockDetector, CourtDetector
from .decision import DecisionEngine
from .utils import draw_detections

class ProcessingEngine:
    def __init__(self):
        self.shuttlecock_detector = ShuttlecockDetector()
        self.court_detector = CourtDetector()
        self.decision_engine = DecisionEngine()

    def process_video(self, video_path, output_path=None, mode="doubles"):
        """
        Processes the video, runs detection, and generates an output video with visualizations.
        Returns a summary of results.
        mode: "singles" or "doubles"
        """
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        if output_path:
            # Use 'avc1' (H.264) for browser compatibility
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

        frame_count = 0
        results_summary = []
        active_decision = None
        decision_timer = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # 1. Detect
            shuttlecock_dets = self.shuttlecock_detector.detect(frame)
            court_dets = self.court_detector.detect(frame)
            
            # 2. Decide
            # Pass frame_count for trajectory tracking
            decision_event = self.decision_engine.evaluate(shuttlecock_dets, court_dets, frame_count, mode=mode)
            
            if decision_event:
                active_decision = decision_event
                decision_timer = 60 # Show for 60 frames (approx 2 seconds)
                results_summary.append(decision_event)

            # 3. Visualize
            frame = draw_detections(frame, shuttlecock_dets, color=(0, 255, 255), label_prefix="Shuttle")
            frame = draw_detections(frame, court_dets, color=(0, 255, 0), label_prefix="Court")
            
            if active_decision and decision_timer > 0:
                # Draw impact point
                center = active_decision["point"]
                cv2.circle(frame, (int(center[0]), int(center[1])), 10, (0, 0, 255), -1)
                
                # Draw decision text
                text = f"{active_decision['decision']}"
                cv2.putText(frame, text, (int(center[0]) + 15, int(center[1])), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                
                decision_timer -= 1

            if output_path:
                out.write(frame)

        cap.release()
        if output_path:
            out.release()

        return results_summary
