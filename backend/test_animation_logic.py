import cv2
import numpy as np
import logging
from processing.animation import AnimationEngine

logging.basicConfig(level=logging.INFO)

def test_animation_generation():
    engine = AnimationEngine()
    
    # Dummy data
    decision = "IN"
    trajectory_2d = [(100, 100), (200, 200), (300, 300), (400, 400), (500, 500)]
    impact_point = (500, 500)
    
    # Mock court info
    court_info = {
        'court_detections': [[100, 200, 800, 900, 0.9, 0]], # x1, y1, x2, y2
        'lines_detected': False,
        'line_detector': None
    }
    
    fps = 30
    width = 1920
    height = 1080
    
    print("Testing generate_hawkeye_replay...")
    generator = engine.generate_hawkeye_replay(
        decision=decision,
        trajectory=trajectory_2d,
        impact_point=impact_point,
        court_info=court_info,
        fps=fps,
        duration=1.0, # Short duration for test
        mode="doubles",
        width=width,
        height=height
    )
    
    frame_count = 0
    try:
        for frame in generator:
            frame_count += 1
            if frame is None:
                print("Error: Generated None frame")
                return
            if frame.shape != (height, width, 3):
                print(f"Error: Invalid frame shape {frame.shape}")
                return
                
        print(f"Success! Generated {frame_count} frames.")
        
    except Exception as e:
        print(f"Exception during generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_animation_generation()
