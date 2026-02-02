import cv2
from pathlib import Path
from .detectors import ShuttlecockDetector, CourtDetector
from .decision import DecisionEngine
from .utils import draw_detections, draw_court_lines
from .line_detector import LineDetector

class ProcessingEngine:
    def __init__(self):
        self.shuttlecock_detector = ShuttlecockDetector()
        self.court_detector = CourtDetector()
        self.decision_engine = DecisionEngine()
        self.line_detector = LineDetector()

    def process_video(self, video_path, output_path=None, mode="doubles", shot_type="rally"):
        """
        Processes the video, runs detection, and generates an output video with visualizations.
        Returns a summary of results.
        mode: "singles" or "doubles"
        shot_type: "serve" or "rally"
        """
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        if output_path:
            # Use 'vp09' (VP9) as fallback for 'avc1' issues
            fourcc = cv2.VideoWriter_fourcc(*'vp09')
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

        frame_count = 0
        results_summary = []
        active_decision = None
        decision_timer = 0
        lines_detected = False
        court_dets = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # 1. Detect
            shuttlecock_dets = self.shuttlecock_detector.detect(frame)
            
            # Court Detection Optimization: Run every 5 frames
            COURT_DETECT_INTERVAL = 5
            if frame_count % COURT_DETECT_INTERVAL == 0 or len(court_dets) == 0:
                 new_court_dets = self.court_detector.detect(frame)
                 if new_court_dets:
                     court_dets = new_court_dets
            
            # 2. Detect lines once when we have court detection (refresh if needed or just keep static logic?)
            # Since camera moves, we might want to re-detect lines if court moved significantly?
            # For now, keeping original logic which only runs ONCE. 
            # TODO: If camera pans, lines need to be re-detected relative to new court box.
            # Ideally, LineDetector should take the court_box every frame.
             
            if not lines_detected and court_dets:
                court_box = court_dets[0][:4]
                self.line_detector.detect_lines(frame, court_box)
                lines_detected = True
            
            # 3. Decide
            # Pass frame_count for trajectory tracking and line_detector for precise boundaries
            decision_event = self.decision_engine.evaluate(
                shuttlecock_dets, 
                court_dets, 
                frame_count, 
                mode=mode, 
                shot_type=shot_type,
                line_detector=self.line_detector if lines_detected else None
            )
            
            if decision_event:
                active_decision = decision_event
                decision_timer = 60 # Show for 60 frames (approx 2 seconds)
                results_summary.append(decision_event)

            # 3. Visualize
            frame = draw_detections(frame, shuttlecock_dets, color=(0, 255, 255), label_prefix="Shuttle")
            frame = draw_detections(frame, court_dets, color=(0, 255, 0), label_prefix="Court")
            
            if lines_detected:
                frame = draw_court_lines(frame, self.line_detector.court_lines, color=(255, 0, 0))
            
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
