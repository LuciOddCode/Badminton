import numpy as np
from collections import deque

class DecisionEngine:
    def __init__(self):
        # History stores tuples of (frame_number, (x, y))
        self.history = deque(maxlen=7)
        self.cooldown = 0

    def is_inside(self, point, box):
        """
        Checks if a point (x, y) is inside a box [x1, y1, x2, y2].
        """
        px, py = point
        x1, y1, x2, y2 = box
        return x1 <= px <= x2 and y1 <= py <= y2

    def evaluate(self, shuttlecock_detections, court_detections, frame_num, mode="doubles"):
        """
        Evaluates the frame to determine if the shuttlecock is IN or OUT based on bounce.
        Returns a dictionary with decision details if a bounce is detected, else None.
        mode: "singles" or "doubles"
        """
        if self.cooldown > 0:
            self.cooldown -= 1
            
        if not shuttlecock_detections:
            return None

        # Track the first detected shuttlecock
        s_box = shuttlecock_detections[0]
        s_center = ((s_box[0] + s_box[2]) / 2, (s_box[1] + s_box[3]) / 2)
        
        self.history.append((frame_num, s_center))
        
        # Need enough history to detect a curve
        if len(self.history) < 5:
            return None
            
        if self.cooldown > 0:
            return None

        # Bounce detection logic:
        # We look for a local maximum in Y (lowest point on screen)
        # History: [p1, p2, p3, p4, p5]
        # We check if p3 is lower (higher Y) than p1, p2 AND p4, p5
        
        # Extract Y coordinates
        y_coords = [p[1][1] for p in self.history]
        
        # Check if the middle point is the lowest (max Y)
        mid_idx = len(y_coords) // 2
        mid_y = y_coords[mid_idx]
        
        # Simple check: mid point is lower than neighbors
        # We use a small threshold to avoid noise
        is_local_max = all(mid_y >= y for y in y_coords) and (mid_y > y_coords[0] + 2) and (mid_y > y_coords[-1] + 2)
        
        if is_local_max:
            # Bounce detected at the middle frame of our history
            bounce_frame, bounce_point = self.history[mid_idx]
            
            # Determine IN/OUT
            is_in = False
            if court_detections:
                for c_box in court_detections:
                    box = c_box[:4]
                    
                    # Adjust for Singles: Narrow the court width
                    if mode == "singles":
                        x1, y1, x2, y2 = box
                        width = x2 - x1
                        # Singles court is narrower (exclude tramlines)
                        # Approx 1.5ft out of 20ft width on each side ~ 7.5%
                        margin = width * 0.075
                        box = [x1 + margin, y1, x2 - margin, y2]
                        
                    if self.is_inside(bounce_point, box):
                        is_in = True
                        break
            
            self.cooldown = 30 # Prevent multiple detections for the same bounce
            
            return {
                "decision": "IN" if is_in else "OUT",
                "point": (float(bounce_point[0]), float(bounce_point[1])),
                "frame": int(bounce_frame)
            }
            
        return None
