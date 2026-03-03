import numpy as np
from collections import deque

class DecisionEngine:
    def __init__(self):
        # History stores tuples of (frame_number, (x, y))
        # Increased buffer for smoother trajectory visualization
        self.history = deque(maxlen=20)
        self.cooldown = 0
    
    def get_trajectory_history(self):
        """Export trajectory history for animation."""
        return list(self.history)

    def is_inside(self, point, box):
        """
        Checks if a point (x, y) is inside a box [x1, y1, x2, y2].
        """
        px, py = point
        x1, y1, x2, y2 = box
        return x1 <= px <= x2 and y1 <= py <= y2

    def evaluate(self, shuttlecock_detections, court_detections, frame_num, mode="doubles", shot_type="rally", line_detector=None):
        """
        Evaluates the frame to determine if the shuttlecock is IN or OUT based on bounce.
        Returns a dictionary with decision details if a bounce is detected, else None.
        mode: "singles" or "doubles"
        shot_type: "serve" or "rally"
        line_detector: LineDetector instance with detected court lines
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
        # OR a landing where the shuttle stops (Y increases then flattens)
        y_coords = [p[1][1] for p in self.history]
        
        # Find the actual lowest point (maximum Y value) in trajectory
        max_y_idx = y_coords.index(max(y_coords))
        max_y = y_coords[max_y_idx]
        
        # Analyze velocities to distinguish floor bounces from racket hits
        # Incoming drop (start -> max): Should be positive (increasing Y)
        dy_in = max_y - y_coords[0]
        # Outgoing rise (max -> end): Should be negative (decreasing Y) or near zero (stop)
        dy_out = y_coords[-1] - max_y
        
        # 1. Must be a significant drop to count as a landing trajectory
        if dy_in < 2.0:
            return None
            
        # 2. Energy Ratio Check:
        # Floor bounce/landing dissipates energy (outgoing speed < incoming speed)
        # Racket hit adds energy (outgoing speed > incoming speed, often significantly)
        # We use displacement as a proxy for speed
        dist_in = abs(dy_in)
        dist_out = abs(dy_out)
        
        # If outgoing move is significantly larger than incoming, it's likely a racket hit (e.g. lift/clear)
        if dist_out > dist_in * 1.5:
             # Likely a racket hit - ignore
             return None

        # 3. Peak/Corner Detection
        # Check if max_y is effectively the local maximum (lowest point)
        # We allow it to be equal to neighbors (for "sticky" landings)
        # but it must be clearly lower (higher Y) than the start.
        
        # PREVENT PREMATURE DETECTION: ensures the shuttle has hit the ground and we've observed 
        # at least 2 frames AFTER the impact. If max_y is at the very end of history, it's still descending.
        frames_after_peak = len(y_coords) - 1 - max_y_idx
        if frames_after_peak < 2:
            return None

        margin = 0.5
        is_peak = all(max_y >= y - margin for y in y_coords) # Relaxed peak check
        
        # Distinctness: Must have dropped significantly
        dropped_in = (max_y >= y_coords[0] + margin)
        
        # For outgoing, we accept either a rise (bounce) OR a flat tail (landing/stop)
        # We reject if it continues to drop significantly (which would mean mid is not the bottom)
        # But `is_peak` already covers that roughly.
        # We just need to ensure it didn't just "drift" down.
        
        is_local_max = is_peak and dropped_in
        
        if is_local_max:
            # Bounce detected at the actual lowest point in our history
            bounce_frame, bounce_point = self.history[max_y_idx]
            
            # Determine IN/OUT using LineDetector if available
            is_in = False
            
            if line_detector and line_detector.court_lines:
                # Use precise line detection
                is_in = line_detector.is_point_in_bounds(bounce_point, mode=mode, shot_type=shot_type)
            elif court_detections:
                # Fallback to old percentage-based method if line detection fails
                for c_box in court_detections:
                    box = c_box[:4]
                    x1, y1, x2, y2 = box
                    
                    # Adjust for Singles: Narrow the court width
                    if mode == "singles":
                        width = x2 - x1
                        margin = width * 0.075
                        box = [x1 + margin, y1, x2 - margin, y2]
                    
                    # Adjust for Doubles Serve: Short Service Line
                    if mode == "doubles" and shot_type == "serve":
                        height = y2 - y1
                        margin_h = height * 0.028
                        box = [box[0], y1 + margin_h, box[2], y2 - margin_h]

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
