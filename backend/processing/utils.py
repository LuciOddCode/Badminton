import cv2
import numpy as np

def get_video_properties(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    
    return {
        "width": width,
        "height": height,
        "fps": fps,
        "frame_count": frame_count
    }

def draw_detections(frame, detections, color=(0, 255, 0), label_prefix="Obj"):
    """
    Draws bounding boxes on the frame.
    detections: list of [x1, y1, x2, y2, conf, cls]
    """
    for det in detections:
        x1, y1, x2, y2, conf, cls = det
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
        label = f"{label_prefix} {conf:.2f}"
        cv2.putText(frame, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return frame

def draw_decision(frame, decision, color=(0, 0, 255)):
    """
    Draws the IN/OUT decision on the frame.
    """
    cv2.putText(frame, f"Decision: {decision}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)
    return frame

def draw_court_lines(frame, court_lines, color=(255, 0, 0)):
    """
    Draws detected court lines on the frame.
    court_lines: Dictionary containing 'inner_sidelines', 'outer_sidelines', 'service_lines', 'baselines'
                 stored as (m, c) tuples.
    """
    height, width = frame.shape[:2]
    
    # Draw Vertical Lines (Sidelines): x = my + c
    for category in ['inner_sidelines', 'outer_sidelines']:
        if court_lines.get(category):
            for m, c in court_lines[category]:
                # y = 0 -> x = c
                # y = height -> x = m*height + c
                pt1 = (int(c), 0)
                pt2 = (int(m * height + c), height)
                cv2.line(frame, pt1, pt2, color, 2)
                
    # Draw Horizontal Lines (Baselines, Service lines): y = mx + c
    for category in ['baselines', 'service_lines']:
        if court_lines.get(category):
            for m, c in court_lines[category]:
                # x = 0 -> y = c
                # x = width -> y = m*width + c
                pt1 = (0, int(c))
                pt2 = (width, int(m * width + c))
                cv2.line(frame, pt1, pt2, color, 2)
                
    return frame
