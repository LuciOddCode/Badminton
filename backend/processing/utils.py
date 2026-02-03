import cv2
import numpy as np

def draw_detections(frame, detections, color=(0, 255, 0), label_prefix="Object"):
    """
    Draws bounding boxes and labels for all detections.
    detections: list of bboxes [x1, y1, x2, y2, conf] or [x1, y1, x2, y2, conf, class]
    """
    for det in detections:
        x1, y1, x2, y2 = map(int, det[:4])
        conf = det[4] if len(det) > 4 else 1.0
        label = f"{label_prefix} {conf:.2f}"
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return frame

def draw_court_lines(frame, lines, color=(255, 0, 0), thickness=2):
    """
    Draws court lines on the frame.
    lines: dict of {name: list of (m, c) tuples representing line equations}
          - For vertical lines: x = m*y + c
          - For horizontal lines: y = m*x + c
    """
    if not lines:
        return frame
    
    height, width = frame.shape[:2]
    
    # Draw vertical lines (sidelines): x = m*y + c
    for line_type in ['inner_sidelines', 'outer_sidelines']:
        if line_type in lines:
            for line_eq in lines[line_type]:
                if len(line_eq) == 2:  # Ensure it's a (m, c) tuple
                    m, c = line_eq
                    # Evaluate at top and bottom of frame
                    y1, y2 = 0, height
                    x1 = int(m * y1 + c)
                    x2 = int(m * y2 + c)
                    cv2.line(frame, (x1, y1), (x2, y2), color, thickness)
    
    # Draw horizontal lines (baselines, service lines): y = m*x + c
    for line_type in ['baselines', 'service_lines']:
        if line_type in lines:
            for line_eq in lines[line_type]:
                if len(line_eq) == 2:  # Ensure it's a (m, c) tuple
                    m, c = line_eq
                    # Evaluate at left and right of frame
                    x1, x2 = 0, width
                    y1 = int(m * x1 + c)
                    y2 = int(m * x2 + c)
                    cv2.line(frame, (x1, y1), (x2, y2), color, thickness)
    
    return frame

def draw_impact_marker(frame, center, decision, timer, max_timer=60):
    """
    Draws an enhanced professional impact point marker for shuttlecock drop.
    
    Args:
        frame: The video frame
        center: (x, y) tuple of the impact point
        decision: "IN" or "OUT"
        timer: Current timer value (counts down from max_timer)
        max_timer: Maximum timer value for animation
    """
    x, y = int(center[0]), int(center[1])
    
    # Color based on decision
    if decision == "IN":
        primary_color = (0, 255, 0)  # Green
        secondary_color = (0, 200, 0)
    else:
        primary_color = (0, 0, 255)  # Red
        secondary_color = (0, 0, 200)
    
    # Animation progress (0.0 to 1.0, where 1.0 is start and 0.0 is end)
    progress = timer / max_timer
    
    # 1. Expanding Ripple Rings (3 waves)
    for i in range(3):
        # Stagger the waves
        wave_progress = (progress + i * 0.33) % 1.0
        radius = int(10 + wave_progress * 40)
        alpha = int(255 * (1 - wave_progress))
        
        # Create semi-transparent effect by adjusting thickness
        thickness = max(1, int(3 * (1 - wave_progress)))
        
        # Draw ring with fading effect
        color_with_alpha = tuple(int(c * (1 - wave_progress * 0.7)) for c in primary_color)
        cv2.circle(frame, (x, y), radius, color_with_alpha, thickness)
    
    # 2. Crosshair
    crosshair_size = 20
    gap = 8  # Gap in the middle for the center point
    thickness_cross = 3
    
    # Horizontal lines
    cv2.line(frame, (x - crosshair_size, y), (x - gap, y), primary_color, thickness_cross)
    cv2.line(frame, (x + gap, y), (x + crosshair_size, y), primary_color, thickness_cross)
    
    # Vertical lines
    cv2.line(frame, (x, y - crosshair_size), (x, y - gap), primary_color, thickness_cross)
    cv2.line(frame, (x, y + gap), (x, y + crosshair_size), primary_color, thickness_cross)
    
    # 3. Center Point (pulsing)
    pulse = 0.8 + 0.2 * np.sin(progress * 10)  # Subtle pulse
    center_radius = int(6 * pulse)
    cv2.circle(frame, (x, y), center_radius, primary_color, -1)
    cv2.circle(frame, (x, y), center_radius + 2, (255, 255, 255), 2)  # White outline
    
    # 4. Corner Brackets (L-shapes at corners)
    bracket_size = 15
    bracket_offset = 25
    bracket_thickness = 2
    
    corners = [
        (x - bracket_offset, y - bracket_offset),  # Top-left
        (x + bracket_offset, y - bracket_offset),  # Top-right
        (x - bracket_offset, y + bracket_offset),  # Bottom-left
        (x + bracket_offset, y + bracket_offset),  # Bottom-right
    ]
    
    # Top-left
    cv2.line(frame, corners[0], (corners[0][0] + bracket_size, corners[0][1]), secondary_color, bracket_thickness)
    cv2.line(frame, corners[0], (corners[0][0], corners[0][1] + bracket_size), secondary_color, bracket_thickness)
    
    # Top-right
    cv2.line(frame, corners[1], (corners[1][0] - bracket_size, corners[1][1]), secondary_color, bracket_thickness)
    cv2.line(frame, corners[1], (corners[1][0], corners[1][1] + bracket_size), secondary_color, bracket_thickness)
    
    # Bottom-left
    cv2.line(frame, corners[2], (corners[2][0] + bracket_size, corners[2][1]), secondary_color, bracket_thickness)
    cv2.line(frame, corners[2], (corners[2][0], corners[2][1] - bracket_size), secondary_color, bracket_thickness)
    
    # Bottom-right
    cv2.line(frame, corners[3], (corners[3][0] - bracket_size, corners[3][1]), secondary_color, bracket_thickness)
    cv2.line(frame, corners[3], (corners[3][0], corners[3][1] - bracket_size), secondary_color, bracket_thickness)
    
    return frame
