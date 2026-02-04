import cv2
import numpy as np
from processing.line_detector import LineDetector

def test_doubles_fallback_logic():
    print("Initialize LineDetector...")
    ld = LineDetector()
    
    # 1. Create a Synthetic Image (Black Background)
    # 1920x1080
    W, H = 1920, 1080
    frame = np.zeros((H, W, 3), dtype=np.uint8)
    
    # Define Court Box (covers most of the frame)
    box_x1, box_y1 = 100, 100
    box_x2, box_y2 = 1820, 980
    court_box = np.array([box_x1, box_y1, box_x2, box_y2])
    court_w = box_x2 - box_x1 # 1720
    
    # 2. Draw ONLY "Inner" Lines (Singles Lines)
    # Real outer lines would be at relative x=0 and x=1720
    # Singles lines are ~10% in. Say at relative 172 and 1548.
    # Absolute x: 100+172=272, 100+1548=1648.
    
    # Draw vertical white lines
    cv2.line(frame, (272, box_y1), (272, box_y2), (255, 255, 255), 5)
    cv2.line(frame, (1648, box_y1), (1648, box_y2), (255, 255, 255), 5)
    
    # Draw baselines (just to satisfy logic if needed, though we focus on vertical)
    cv2.line(frame, (box_x1, box_y1), (box_x2, box_y1), (255, 255, 255), 5)
    cv2.line(frame, (box_x1, box_y2), (box_x2, box_y2), (255, 255, 255), 5)
    
    print("Running detect_lines on synthetic image (Only inner lines visible)...")
    ld.detect_lines(frame, court_box)
    
    outer_lines = ld.court_lines['outer_sidelines']
    if not outer_lines:
        print("No lines detected!")
        return

    # Check width of detected outer lines
    # outer_lines is list of (m, c). x = my + c.
    # Evaluate at mid Y
    mid_y = (box_y1 + box_y2) / 2
    
    x_left = outer_lines[0][0] * mid_y + outer_lines[0][1]
    x_right = outer_lines[1][0] * mid_y + outer_lines[1][1]
    
    detected_width = x_right - x_left
    print(f"Court Box Width: {court_w}")
    print(f"Detected Outer Width: {detected_width:.2f}")
    
    # Point in Alley: Absolute X = 150 (Inside box 100, but Left of Inner Line 272)
    # Should be IN.
    pt = (150, 500)
    is_in = ld.is_point_in_bounds(pt, mode="doubles")
    print(f"Point {pt} Prediction: {'IN' if is_in else 'OUT'}")
    
    # Assertion
    ratio = detected_width / court_w
    print(f"Width Ratio: {ratio:.2f}")
    
    with open("test_result.txt", "w") as f:
        if ratio < 0.90:
            msg = f"FAIL: Detected lines are too narrow (Ratio={ratio:.2f})."
            print(msg)
            f.write(msg)
        else:
            msg = f"SUCCESS: Detected lines match court width (Ratio={ratio:.2f}). Fallback applied."
            print(msg)
            f.write(msg)

if __name__ == "__main__":
    test_doubles_fallback_logic()
