import cv2
import numpy as np
from collections import defaultdict

class LineDetector:
    def __init__(self):
        self.detected_lines = None
        self.court_lines = {
            'inner_sidelines': [],  # Singles sidelines
            'outer_sidelines': [],  # Doubles sidelines
            'service_lines': [],    # Short and long service lines
            'baselines': []         # Back boundaries
        }
    
    def detect_lines(self, frame, court_box):
        """
        Detect white court lines within the court bounding box.
        
        Args:
            frame: Input video frame
            court_box: [x1, y1, x2, y2] bounding box of the court
            
        Returns:
            Dictionary of classified lines
        """
        x1, y1, x2, y2 = map(int, court_box[:4])
        
        # Extract court region
        court_region = frame[y1:y2, x1:x2]
        
        # Preprocessing
        gray = cv2.cvtColor(court_region, cv2.COLOR_BGR2GRAY)
        
        # Apply bilateral filter to reduce noise while keeping edges sharp
        blurred = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Edge detection
        edges = cv2.Canny(blurred, 50, 150, apertureSize=3)
        
        # Hough Line Transform
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=100,
            minLineLength=50,
            maxLineGap=10
        )
        
        if lines is None:
            return self.court_lines
        
        # Classify lines
        vertical_lines = []
        horizontal_lines = []
        
        for line in lines:
            x1_l, y1_l, x2_l, y2_l = line[0]
            
            # Calculate angle
            angle = np.abs(np.arctan2(y2_l - y1_l, x2_l - x1_l) * 180 / np.pi)
            
            # Classify as vertical or horizontal
            if angle > 80 and angle < 100:  # Nearly vertical (sidelines)
                vertical_lines.append(line[0])
            elif angle < 10 or angle > 170:  # Nearly horizontal (service/base lines)
                horizontal_lines.append(line[0])
        
        # Merge similar lines and classify
        self._classify_vertical_lines(vertical_lines, court_region.shape[1])
        self._classify_horizontal_lines(horizontal_lines, court_region.shape[0])
        
        # Adjust coordinates back to full frame
        self._adjust_to_frame_coords(x1, y1)
        
        return self.court_lines
    
    def _classify_vertical_lines(self, lines, width):
        """Classify vertical lines as inner or outer sidelines"""
        if not lines:
            return
        
        # Group lines by x-coordinate (average of x1 and x2)
        line_positions = [(l[0] + l[2]) / 2 for l in lines]
        
        # Find unique positions (merge similar lines)
        unique_positions = []
        for pos in sorted(line_positions):
            if not unique_positions or abs(pos - unique_positions[-1]) > 20:
                unique_positions.append(pos)
        
        # Sort positions
        unique_positions.sort()
        
        # Classify based on position
        # Typically: outer_left, inner_left, inner_right, outer_right
        if len(unique_positions) >= 4:
            self.court_lines['outer_sidelines'] = [unique_positions[0], unique_positions[-1]]
            self.court_lines['inner_sidelines'] = [unique_positions[1], unique_positions[-2]]
        elif len(unique_positions) >= 2:
            # Assume we only see inner or outer lines
            self.court_lines['outer_sidelines'] = [unique_positions[0], unique_positions[-1]]
            self.court_lines['inner_sidelines'] = [unique_positions[0], unique_positions[-1]]
    
    def _classify_horizontal_lines(self, lines, height):
        """Classify horizontal lines as service lines or baselines"""
        if not lines:
            return
        
        # Group lines by y-coordinate
        line_positions = [(l[1] + l[3]) / 2 for l in lines]
        
        # Find unique positions
        unique_positions = []
        for pos in sorted(line_positions):
            if not unique_positions or abs(pos - unique_positions[-1]) > 20:
                unique_positions.append(pos)
        
        unique_positions.sort()
        
        # Classify: baselines are at top and bottom, service lines in middle
        if len(unique_positions) >= 2:
            self.court_lines['baselines'] = [unique_positions[0], unique_positions[-1]]
            if len(unique_positions) > 2:
                self.court_lines['service_lines'] = unique_positions[1:-1]
    
    def _adjust_to_frame_coords(self, offset_x, offset_y):
        """Adjust line coordinates from court region to full frame coordinates"""
        # Adjust vertical lines (x-coordinates)
        if self.court_lines['outer_sidelines']:
            self.court_lines['outer_sidelines'] = [x + offset_x for x in self.court_lines['outer_sidelines']]
        if self.court_lines['inner_sidelines']:
            self.court_lines['inner_sidelines'] = [x + offset_x for x in self.court_lines['inner_sidelines']]
        
        # Adjust horizontal lines (y-coordinates)
        if self.court_lines['baselines']:
            self.court_lines['baselines'] = [y + offset_y for y in self.court_lines['baselines']]
        if self.court_lines['service_lines']:
            self.court_lines['service_lines'] = [y + offset_y for y in self.court_lines['service_lines']]
    
    def is_point_in_bounds(self, point, mode="doubles", shot_type="rally"):
        """
        Check if a point is within the court boundaries based on detected lines.
        
        Args:
            point: (x, y) tuple
            mode: "singles" or "doubles"
            shot_type: "serve" or "rally"
            
        Returns:
            bool: True if point is IN, False if OUT
        """
        x, y = point
        
        # Determine which sidelines to use
        if mode == "singles":
            if not self.court_lines['inner_sidelines'] or len(self.court_lines['inner_sidelines']) < 2:
                return False
            left_line = self.court_lines['inner_sidelines'][0]
            right_line = self.court_lines['inner_sidelines'][1]
        else:  # doubles
            if not self.court_lines['outer_sidelines'] or len(self.court_lines['outer_sidelines']) < 2:
                return False
            left_line = self.court_lines['outer_sidelines'][0]
            right_line = self.court_lines['outer_sidelines'][1]
        
        # Check horizontal bounds (sidelines)
        if x < left_line or x > right_line:
            return False
        
        # Check vertical bounds (baselines and service lines)
        if not self.court_lines['baselines'] or len(self.court_lines['baselines']) < 2:
            return False
        
        top_line = self.court_lines['baselines'][0]
        bottom_line = self.court_lines['baselines'][1]
        
        # For doubles serve, check service lines
        if mode == "doubles" and shot_type == "serve":
            if self.court_lines['service_lines']:
                # Service area is between service lines (not all the way to baseline)
                # Adjust the boundaries to exclude back tramline
                # Assuming service lines are between baselines
                if len(self.court_lines['service_lines']) >= 1:
                    # Use service lines as new boundaries for serve
                    # This is a simplified approach - might need refinement
                    top_line = min(self.court_lines['service_lines'])
                    bottom_line = max(self.court_lines['service_lines'])
        
        # Check if point is between top and bottom lines
        if y < top_line or y > bottom_line:
            return False
        
        return True
