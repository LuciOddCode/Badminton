import numpy as np

class DecisionEngine:
    def __init__(self):
        pass

    def is_inside(self, point, box):
        """
        Checks if a point (x, y) is inside a box [x1, y1, x2, y2].
        """
        px, py = point
        x1, y1, x2, y2 = box
        return x1 <= px <= x2 and y1 <= py <= y2

    def evaluate(self, shuttlecock_detections, court_detections):
        """
        Evaluates the frame to determine if the shuttlecock is IN or OUT.
        Returns "IN", "OUT", or None (if no shuttlecock/court detected).
        
        This is a simplified logic:
        - If shuttlecock center is inside ANY court box -> IN
        - Else -> OUT
        """
        if not shuttlecock_detections or not court_detections:
            return None

        # Assume the first detection is the relevant one for now
        # Shuttlecock center
        s_box = shuttlecock_detections[0]
        s_center = ((s_box[0] + s_box[2]) / 2, (s_box[1] + s_box[3]) / 2)

        is_in = False
        for c_box in court_detections:
            # Court box: [x1, y1, x2, y2, ...]
            # We only care about the coordinates
            if self.is_inside(s_center, c_box[:4]):
                is_in = True
                break
        
        return "IN" if is_in else "OUT"
