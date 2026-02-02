import cv2
import numpy as np

class LineDetector:
    def __init__(self):
        self.detected_lines = None
        # Store lines as fitted line coefficients:
        # vertical lines: x = my + c -> (m, c)
        # horizontal lines: y = mx + c -> (m, c)
        self.court_lines = {
            'inner_sidelines': [],  # List of (m, c) for x = my + c
            'outer_sidelines': [],  # List of (m, c)
            'service_lines': [],    # List of (m, c) for y = mx + c
            'baselines': []         # List of (m, c)
        }
    
    def detect_lines(self, frame, court_box):
        """
        Detect white court lines within the court bounding box.
        """
        x1_box, y1_box, x2_box, y2_box = map(int, court_box[:4])
        
        # Extract court region
        court_region = frame[y1_box:y2_box, x1_box:x2_box]
        region_h, region_w = court_region.shape[:2]
        
        # Preprocessing
        gray = cv2.cvtColor(court_region, cv2.COLOR_BGR2GRAY)
        blurred = cv2.bilateralFilter(gray, 9, 75, 75)
        edges = cv2.Canny(blurred, 50, 150, apertureSize=3)
        
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=80,      # Lower threshold to catch faint lines
            minLineLength=50,
            maxLineGap=20
        )
        
        # Reset
        self.court_lines = {k: [] for k in self.court_lines}
        
        if lines is None:
            return self.court_lines
        
        vertical_segments = []
        horizontal_segments = []
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            dx = x2 - x1
            dy = y2 - y1
            
            angle = np.abs(np.arctan2(dy, dx) * 180 / np.pi)
            
            # Relaxed angle constraints for perspective
            if angle > 60 and angle < 120:  # Vertical-ish
                vertical_segments.append((x1, y1, x2, y2))
            elif angle < 30 or angle > 150: # Horizontal-ish
                horizontal_segments.append((x1, y1, x2, y2))
        
        self._process_vertical_lines(vertical_segments, region_w, region_h, x1_box, y1_box)
        self._process_horizontal_lines(horizontal_segments, region_w, region_h, x1_box, y1_box)
        
        return self.court_lines

    def _process_vertical_lines(self, segments, w, h, offset_x, offset_y):
        if not segments:
            return
            
        # Group by X-intercept at mid-height to handle perspective
        mid_y = h / 2
        
        # Calculate x_at_mid_y for each segment
        segment_groups = [] # (x_mid, [list of points])
        
        for s in segments:
            x1, y1, x2, y2 = s
            # Avoid division by zero
            if y2 == y1: continue
            
            # x = my + c
            # slope m = dx/dy
            m = (x2 - x1) / (y2 - y1)
            c = x1 - m * y1
            
            x_mid = m * mid_y + c
            segment_groups.append({'x_mid': x_mid, 'points': [(x1, y1), (x2, y2)]})

        # Cluster segments
        segment_groups.sort(key=lambda x: x['x_mid'])
        
        clusters = []
        if segment_groups:
            current_cluster = [segment_groups[0]]
            for i in range(1, len(segment_groups)):
                # If gap is small, add to cluster
                if segment_groups[i]['x_mid'] - segment_groups[i-1]['x_mid'] < w * 0.1: # 10% width threshold
                    current_cluster.append(segment_groups[i])
                else:
                    clusters.append(current_cluster)
                    current_cluster = [segment_groups[i]]
            clusters.append(current_cluster)
            
        # Fit lines for each cluster
        final_lines = []
        for cluster in clusters:
            all_x = []
            all_y = []
            for item in cluster:
                for pt in item['points']:
                    all_x.append(pt[0] + offset_x)
                    all_y.append(pt[1] + offset_y)
            
            # Fit x = my + c
            if len(all_x) >= 2:
                # polyfit(y, x, 1) returns [m, c]
                m, c = np.polyfit(all_y, all_x, 1)
                final_lines.append((m, c))
        
        # Sort by x-position at frame mid-height (approx offset_y + mid_y)
        # We use x-intercept at y=0 (c) if slopes are similar, or evaluate at mid screen y
        # Evaluating at frame mid Y is safest
        frame_mid_y = offset_y + h/2
        final_lines.sort(key=lambda l: l[0]*frame_mid_y + l[1])

        if len(final_lines) >= 4:
            self.court_lines['outer_sidelines'] = [final_lines[0], final_lines[-1]]
            self.court_lines['inner_sidelines'] = [final_lines[1], final_lines[-2]]
        elif len(final_lines) >= 2:
            self.court_lines['outer_sidelines'] = [final_lines[0], final_lines[-1]]
            self.court_lines['inner_sidelines'] = [final_lines[0], final_lines[-1]]

    def _process_horizontal_lines(self, segments, w, h, offset_x, offset_y):
        if not segments:
            return
            
        # Group by Y-intercept at mid-width
        mid_x = w / 2
        segment_groups = []
        
        for s in segments:
            x1, y1, x2, y2 = s
            if x2 == x1: continue
            
            # y = mx + c
            m = (y2 - y1) / (x2 - x1)
            c = y1 - m * x1
            y_mid = m * mid_x + c
            segment_groups.append({'y_mid': y_mid, 'points': [(x1, y1), (x2, y2)]})
            
        segment_groups.sort(key=lambda x: x['y_mid'])
        
        clusters = []
        if segment_groups:
            current_cluster = [segment_groups[0]]
            for i in range(1, len(segment_groups)):
                if segment_groups[i]['y_mid'] - segment_groups[i-1]['y_mid'] < h * 0.1:
                    current_cluster.append(segment_groups[i])
                else:
                    clusters.append(current_cluster)
                    current_cluster = [segment_groups[i]]
            clusters.append(current_cluster)
            
        final_lines = []
        for cluster in clusters:
            all_x = []
            all_y = []
            for item in cluster:
                for pt in item['points']:
                    all_x.append(pt[0] + offset_x)
                    all_y.append(pt[1] + offset_y)
            
            if len(all_x) >= 2:
                m, c = np.polyfit(all_x, all_y, 1)
                final_lines.append((m, c))
                
        # Sort by y-intercept (c) or y at mid-x
        frame_mid_x = offset_x + w/2
        final_lines.sort(key=lambda l: l[0]*frame_mid_x + l[1])
        
        if len(final_lines) >= 2:
            self.court_lines['baselines'] = [final_lines[0], final_lines[-1]]
            if len(final_lines) > 2:
                # Middle ones are service lines
                self.court_lines['service_lines'] = final_lines[1:-1]

    def is_point_in_bounds(self, point, mode="doubles", shot_type="rally"):
        """
        Check if point (x,y) is inside boundaries. 
        Uses fitted line equations.
        """
        px, py = point
        
        # 1. Check Sidelines (Vertical-ish: x = my + c)
        if mode == "singles":
            lines = self.court_lines['inner_sidelines']
        else:
            lines = self.court_lines['outer_sidelines']
            
        if not lines or len(lines) < 2:
            return False
            
        # Calculate boundary X at this Y
        left_m, left_c = lines[0]
        right_m, right_c = lines[1]
        
        left_bound_x = left_m * py + left_c
        right_bound_x = right_m * py + right_c
        
        if px < left_bound_x or px > right_bound_x:
            return False
            
        # 2. Check Baselines (Horizontal-ish: y = mx + c)
        baselines = self.court_lines['baselines']
        if not baselines or len(baselines) < 2:
            return False
            
        top_m, top_c = baselines[0]
        bot_m, bot_c = baselines[1]
        
        top_bound_y = top_m * px + top_c
        bot_bound_y = bot_m * px + bot_c
        
        if py < top_bound_y or py > bot_bound_y:
            return False
            
        return True
