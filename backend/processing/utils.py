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
    """
    height, width = frame.shape[:2]
    
    # Determine boundaries for drawing
    x_min, x_max = 0, width
    y_min, y_max = 0, height
    
    if court_lines.get('outer_sidelines'):
        x_min = int(min(court_lines['outer_sidelines']))
        x_max = int(max(court_lines['outer_sidelines']))
        
    if court_lines.get('baselines'):
        y_min = int(min(court_lines['baselines']))
        y_max = int(max(court_lines['baselines']))
    
    # Draw Vertical Lines (Sidelines)
    # They span from top baseline to bottom baseline
    for category in ['inner_sidelines', 'outer_sidelines']:
        if court_lines.get(category):
            for x in court_lines[category]:
                pt1 = (int(x), y_min)
                pt2 = (int(x), y_max)
                cv2.line(frame, pt1, pt2, color, 2)
                
    # Draw Horizontal Lines (Baselines, Service lines)
    # They span from left outer sideline to right outer sideline
    for category in ['baselines', 'service_lines']:
        if court_lines.get(category):
            for y in court_lines[category]:
                pt1 = (x_min, int(y))
                pt2 = (x_max, int(y))
                cv2.line(frame, pt1, pt2, color, 2)
                
    return frame
