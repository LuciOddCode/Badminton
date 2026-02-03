import cv2
from pathlib import Path
import logging
from .detectors import ShuttlecockDetector, CourtDetector
from .decision import DecisionEngine
from .utils import draw_detections, draw_court_lines, draw_impact_marker
from .line_detector import LineDetector
from .animation import AnimationEngine

logger = logging.getLogger(__name__)

class ProcessingEngine:
    def __init__(self):
        logger.info("Initializing ProcessingEngine...")
        self.shuttlecock_detector = ShuttlecockDetector()
        self.court_detector = CourtDetector()
        self.decision_engine = DecisionEngine()
        self.line_detector = LineDetector()
        self.animation_engine = AnimationEngine()
        logger.info("ProcessingEngine initialized.")

    def process_video(self, video_path, output_path=None, mode="doubles", shot_type="rally"):
        """
        Processes the video, runs detection, and generates an output video with visualizations.
        Returns a summary of results.
        mode: "singles" or "doubles"
        shot_type: "serve" or "rally"
        """
        logger.info(f"Opening video: {video_path}")
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.error(f"Could not open video: {video_path}")
            raise ValueError(f"Could not open video: {video_path}")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        logger.info(f"Video props: {width}x{height} @ {fps}fps")
        
        if output_path:
            # Use 'vp09' (VP9) as fallback for 'avc1' issues
            fourcc = cv2.VideoWriter_fourcc(*'vp09')
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            logger.info(f"Output writer initialized: {output_path}")

        frame_count = 0
        results_summary = []
        active_decision = None
        decision_timer = 0
        lines_detected = False
        court_dets = []
        last_frame = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            last_frame = frame.copy()
            
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
                logger.info(f"Lines detected at frame {frame_count}")
            
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
                if not active_decision:
                    logger.info(f"Decision made at frame {frame_count}: {decision_event}")
                active_decision = decision_event
                decision_timer = 60 # Show for 60 frames (approx 2 seconds)
                results_summary.append(decision_event)

            # 3. Visualize
            frame = draw_detections(frame, shuttlecock_dets, color=(0, 255, 255), label_prefix="Shuttle")
            frame = draw_detections(frame, court_dets, color=(0, 255, 0), label_prefix="Court")
            
            if lines_detected:
                frame = draw_court_lines(frame, self.line_detector.court_lines, color=(255, 0, 0))
            
            if active_decision and decision_timer > 0:
                # Draw enhanced impact point marker
                center = active_decision["point"]
                decision_text = active_decision["decision"]
                frame = draw_impact_marker(frame, center, decision_text, decision_timer, max_timer=60)
                
                # Draw decision text next to the marker
                text = f"{decision_text}"
                cv2.putText(frame, text, (int(center[0]) + 40, int(center[1])), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
                cv2.putText(frame, text, (int(center[0]) + 40, int(center[1])), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.2, 
                           (0, 255, 0) if decision_text == "IN" else (0, 0, 255), 2)
                
                decision_timer -= 1

            if output_path:
                out.write(frame)

        # Append Animation at the end if a decision was made
        if output_path and results_summary:
            # Use the last decision made in the clip
            final_decision = results_summary[-1]["decision"]
            final_impact_point = results_summary[-1]["point"]
            
            logger.info(f"Generating 3D Hawk-Eye replay for decision: {final_decision}")
            
            # Extract trajectory data from decision engine
            trajectory_history = self.decision_engine.get_trajectory_history()
            # Convert to simple (x, y) list
            trajectory_2d = [point for frame_num, point in trajectory_history]
            
            if not trajectory_2d:
                 logger.warning("No trajectory data available for animation")

            # Get court info
            court_info = {
                'court_detections': court_dets,
                'lines_detected': lines_detected,
                'line_detector': self.line_detector if lines_detected else None
            }
            
            # Generate frames using new 3D animation
            # Use last_frame as background fallback (not used in 3D render but kept for compatibility)
            if last_frame is None:
                logger.warning("No frames read from video, creating blank frame for animation fallback")
                last_frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            try:
                anim_generator = self.animation_engine.generate_hawkeye_replay(
                    decision=final_decision,
                    trajectory=trajectory_2d,
                    impact_point=final_impact_point,
                    court_info=court_info,
                    fps=fps,
                    duration=4.0,
                    mode=mode,
                    width=width,
                    height=height
                )
                
                anim_frame_count = 0
                for anim_frame in anim_generator:
                    out.write(anim_frame)
                    anim_frame_count += 1
                logger.info(f"Animation generation complete. {anim_frame_count} frames added.")
            except Exception as e:
                logger.error(f"Error during animation generation: {e}", exc_info=True)
                # Don't fail the whole process if animation fails, just log it
            
        cap.release()
        if output_path:
            out.release()
        
        logger.info(f"Video processing finished. Total frames: {frame_count}")
        return results_summary
