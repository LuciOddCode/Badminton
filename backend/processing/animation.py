import cv2
import numpy as np
import math
import logging
from scipy.interpolate import interp1d
from scipy.optimize import curve_fit

logger = logging.getLogger(__name__)

class Camera3D:
    """Manages 3D camera position, orientation, and perspective projection."""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.fov = 60  # Field of view in degrees
        self.aspect_ratio = width / height
        
    def set_position(self, x, y, z, pitch, yaw=0):
        """
        Set camera position and orientation.
        pitch: rotation around X-axis (0=looking forward, 90=looking down)
        yaw: rotation around Y-axis
        """
        self.pos = np.array([x, y, z], dtype=float)
        self.pitch = pitch  # degrees
        self.yaw = yaw
        
    def project_point(self, point_3d):
        """
        Project a 3D point to 2D screen coordinates.
        Returns (x, y) in screen space, or None if behind camera.
        """
        # Translate to camera space
        p = point_3d - self.pos
        
        # Rotate based on camera orientation
        # Pitch rotation (around X-axis)
        pitch_rad = math.radians(-self.pitch)
        cos_p, sin_p = math.cos(pitch_rad), math.sin(pitch_rad)
        y_rot = p[1] * cos_p - p[2] * sin_p
        z_rot = p[1] * sin_p + p[2] * cos_p
        
        # Yaw rotation (around Y-axis)
        yaw_rad = math.radians(self.yaw)
        cos_y, sin_y = math.cos(yaw_rad), math.sin(yaw_rad)
        x_final = p[0] * cos_y + z_rot * sin_y
        z_final = -p[0] * sin_y + z_rot * cos_y
        y_final = y_rot
        
        # Check if point is behind camera
        if z_final <= 0.1:
            return None
            
        # Perspective projection
        fov_rad = math.radians(self.fov)
        f = 1.0 / math.tan(fov_rad / 2.0)
        
        x_ndc = (x_final * f) / (z_final * self.aspect_ratio)
        y_ndc = (y_final * f) / z_final
        
        # Convert to screen coordinates
        x_screen = int((x_ndc + 1) * self.width / 2)
        y_screen = int((1 - y_ndc) * self.height / 2)
        
        return (x_screen, y_screen)


class Court3DModel:
    """Generates 3D badminton court geometry."""
    
    # Badminton court dimensions in meters
    COURT_LENGTH = 13.4
    COURT_WIDTH_DOUBLES = 6.1
    COURT_WIDTH_SINGLES = 5.18
    SERVICE_LINE_DISTANCE = 1.98  # from net
    SHORT_SERVICE_LINE = 1.98  # from net
    
    def __init__(self):
        self.vertices = []
        self.lines = []
        
    def generate(self, mode="doubles"):
        """Generate court vertices and line segments."""
        width = self.COURT_WIDTH_DOUBLES if mode == "doubles" else self.COURT_WIDTH_SINGLES
        length = self.COURT_LENGTH
        
        # Center court at origin on XZ plane (Y is up)
        half_w = width / 2
        half_l = length / 2
        
        # Court floor vertices (Y=0)
        corners = [
            [-half_w, 0, -half_l],  # Back-left
            [half_w, 0, -half_l],   # Back-right
            [half_w, 0, half_l],    # Front-right
            [-half_w, 0, half_l],   # Front-left
        ]
        
        # Court lines (white lines on green court)
        self.lines = {
            'outer_boundary': [
                (corners[0], corners[1]),  # Back line
                (corners[1], corners[2]),  # Right sideline
                (corners[2], corners[3]),  # Front line
                (corners[3], corners[0]),  # Left sideline
            ],
            'center_line': [
                ([0, 0, -half_l], [0, 0, half_l]),  # Center line
            ],
            'service_lines': []
        }
        
        # Service lines
        service_z = half_l - self.SHORT_SERVICE_LINE
        self.lines['service_lines'].append(
            ([-half_w, 0, -service_z], [half_w, 0, -service_z])
        )
        self.lines['service_lines'].append(
            ([-half_w, 0, service_z], [half_w, 0, service_z])
        )
        
        # Singles court inner lines if in doubles mode
        if mode == "doubles":
            singles_w = self.COURT_WIDTH_SINGLES / 2
            self.lines['singles_sidelines'] = [
                ([-singles_w, 0, -half_l], [-singles_w, 0, half_l]),
                ([singles_w, 0, -half_l], [singles_w, 0, half_l]),
            ]
        
        return corners
    
    def get_floor_grid(self, mode="doubles"):
        """Generate a grid pattern for the court floor."""
        width = self.COURT_WIDTH_DOUBLES if mode == "doubles" else self.COURT_WIDTH_SINGLES
        length = self.COURT_LENGTH
        
        half_w = width / 2
        half_l = length / 2
        
        # Create a simple quad for the floor
        floor_quad = [
            [-half_w, 0, -half_l],
            [half_w, 0, -half_l],
            [half_w, 0, half_l],
            [-half_w, 0, half_l],
        ]
        
        return floor_quad


class TrajectoryRenderer:
    """Renders shuttlecock trajectory with glowing trail effect."""
    
    def __init__(self):
        self.trail_color = (0, 255, 255)  # Yellow in BGR
        self.shuttle_color = (255, 255, 255)  # White
        
    def render(self, frame, trajectory_3d, camera, current_progress, total_frames, current_frame):
        """
        Render trajectory trail on frame with ghost effect near impact.
        trajectory_3d: list of (x, y, z) points
        current_progress: 0.0 to 1.0, how much of trajectory to show
        current_frame: current animation frame number
        total_frames: total frames in trajectory phase
        """
        if len(trajectory_3d) < 2:
            return frame
            
        # Determine how many points to show
        num_points = max(2, int(len(trajectory_3d) * current_progress))
        visible_trajectory = trajectory_3d[:num_points]
        
        # Project to 2D
        projected_points = []
        for pt_3d in visible_trajectory:
            pt_2d = camera.project_point(np.array(pt_3d))
            if pt_2d:
                projected_points.append(pt_2d)
        
        if len(projected_points) < 2:
            return frame
        
        # Draw trail with fading effect and motion blur
        overlay = frame.copy()
        
        for i in range(len(projected_points) - 1):
            # Alpha/intensity decreases towards the start of the trail
            alpha = (i + 1) / len(projected_points)
            thickness = int(2 + alpha * 4)
            
            # Color intensity
            color = tuple(int(c * (0.3 + alpha * 0.7)) for c in self.trail_color)
            
            cv2.line(overlay, projected_points[i], projected_points[i + 1], color, thickness, cv2.LINE_AA)
        
        # Apply Gaussian blur for motion blur effect on trail
        blurred = cv2.GaussianBlur(overlay, (15, 15), 0)
        cv2.addWeighted(blurred, 0.6, frame, 0.4, 0, frame)
        
        # Draw shuttlecock at end of trail with ghost effect
        if projected_points:
            last_point = projected_points[-1]
            
            # Calculate ghost transparency (fade in last 5 frames before impact)
            frames_from_end = total_frames - current_frame
            if frames_from_end <= 5:
                # Gradually become transparent
                alpha = frames_from_end / 5.0
            else:
                alpha = 1.0
            
            # Draw shuttle with transparency
            shuttle_overlay = frame.copy()
            cv2.circle(shuttle_overlay, last_point, 8, self.shuttle_color, -1, cv2.LINE_AA)
            cv2.circle(shuttle_overlay, last_point, 10, self.trail_color, 2, cv2.LINE_AA)
            cv2.addWeighted(shuttle_overlay, alpha, frame, 1 - alpha, 0, frame)
        
        return frame


class AnimationEngine:
    def __init__(self):
        pass

    def _draw_rounded_rect(self, img, pt1, pt2, color, thickness, r, filled=False):
        """
        Draws a rounded rectangle using lines and ellipses.
        """
        x1, y1 = pt1
        x2, y2 = pt2
        
        # Check if radius is too big
        width = x2 - x1
        height = y2 - y1
        r = min(r, width // 2, height // 2)

        # Draw straight parts
        if filled:
            # Main central rects
            cv2.rectangle(img, (x1 + r, y1), (x2 - r, y2), color, -1)
            cv2.rectangle(img, (x1, y1 + r), (x2, y2 - r), color, -1)
            # Four corners
            cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, -1)
            cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, -1)
            cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, -1)
            cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, -1)
        else:
            cv2.line(img, (x1 + r, y1), (x2 - r, y1), color, thickness)
            cv2.line(img, (x1 + r, y2), (x2 - r, y2), color, thickness)
            cv2.line(img, (x1, y1 + r), (x1, y2 - r), color, thickness)
            cv2.line(img, (x2, y1 + r), (x2, y2 - r), color, thickness)
            cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness)
            cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness)
            cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, thickness)
            cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, thickness)

    def generate_hawkeye_replay(self, decision, trajectory, impact_point, court_info, fps, duration=4.0, mode="doubles", width=1920, height=1080):
        """
        Generates a professional 3D Hawk-Eye style replay animation.
        
        Args:
            decision: "IN" or "OUT"
            trajectory: List of (x, y) tuples representing 2D shuttlecock positions
            impact_point: (x, y) tuple of the impact location
            court_info: Dict with court boundary information
            fps: Frames per second
            duration: Animation duration in seconds
            mode: "singles" or "doubles"
            width: Video width in pixels (defaults to 1920)
            height: Video height in pixels (defaults to 1080)
        """
        total_frames = int(fps * duration)
        
        # Animation phases (in frames)
        PHASE_CAMERA_ZOOM = 40  # Frames 0-40: Camera zooms in
        PHASE_TRAJECTORY = 60   # Frames 0-60: Show trajectory
        PHASE_IMPACT = 70       # Frame 70: Impact
        PHASE_VERDICT = total_frames  # Frames 70+: Show verdict
        
        # Use provided video dimensions instead of hardcoded values
        # Setup base frame dimensions
        
        # Initialize 3D components
        camera = Camera3D(width, height)
        court_model = Court3DModel()
        court_model.generate(mode=mode)
        trajectory_renderer = TrajectoryRenderer()
        
        # Convert 2D trajectory to 3D with parabolic curve fitting
        trajectory_3d = self._convert_trajectory_to_3d_parabolic(trajectory, impact_point, width, height)
        
        # Camera animation: S-curve interpolation from stadium view to top-down
        camera_positions = self._generate_camera_path_scurve(total_frames, PHASE_CAMERA_ZOOM)
        
        for frame_idx in range(total_frames):
            # Create blank frame
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Set camera for this frame
            cam_pos, cam_pitch = camera_positions[frame_idx]
            camera.set_position(cam_pos[0], cam_pos[1], cam_pos[2], cam_pitch)
            
            # 1. Render court floor (broadcast green #238363)
            frame = self._render_court_floor(frame, court_model, camera, mode)
            
            # 2. Render court lines (white)
            frame = self._render_court_lines(frame, court_model, camera)
            
            # 3. Render trajectory trail (up to current frame)
            if frame_idx < PHASE_TRAJECTORY:
                progress = frame_idx / PHASE_TRAJECTORY
                frame = trajectory_renderer.render(frame, trajectory_3d, camera, progress, 
                                                  PHASE_TRAJECTORY, frame_idx)
            
            # 4. Impact effect with fixed contact mark
            if frame_idx >= PHASE_IMPACT:
                frame = self._render_impact_effect(frame, impact_point, trajectory_3d, camera, 
                                                   frame_idx - PHASE_IMPACT)
            
            # 5. Verdict display with drop shadow
            if frame_idx >= PHASE_IMPACT + 10:
                frame = self._render_verdict_with_shadow(frame, decision, width, height)
            
            # 6. Add branding
            frame = self._add_branding(frame, width, height)
            
            yield frame
    
    def _parabolic_function(self, x, a, b, c):
        """Quadratic function for curve fitting."""
        return a * x**2 + b * x + c
    
    def _convert_trajectory_to_3d_parabolic(self, trajectory_2d, impact_point, width=1920, height=1080):
        """
        Convert 2D screen-space trajectory to 3D world coordinates using parabolic curve fitting.
        width, height: Video dimensions for proper coordinate normalization
        """
        if not trajectory_2d or len(trajectory_2d) < 3:
            # Fallback: create simple parabolic drop trajectory
            return [
                [0, 3, -2],
                [0, 2.5, -1],
                [0, 1.5, 0],
                [0, 0.5, 1],
                [0, 0, 2],
            ]
        
        # Prepare data for curve fitting
        num_points = len(trajectory_2d)
        x_indices = np.arange(num_points)
        y_coords = np.array([y for x, y in trajectory_2d])
        
        # Fit parabola to Y coordinates (height)
        try:
            # Fit quadratic curve
            popt, _ = curve_fit(self._parabolic_function, x_indices, y_coords, 
                               p0=[-1, 0, max(y_coords)])
            a, b, c = popt
        except:
            # Fallback if curve fitting fails
            a, b, c = -0.1, 0, max(y_coords)
        
        # Fit parabola to X coordinates (lateral movement) to remove "snake" jitter
        x_coords = np.array([x for x, y in trajectory_2d])
        try:
            # Fit quadratic curve to X vs Time (indices)
            popt_x, _ = curve_fit(self._parabolic_function, x_indices, x_coords, 
                                 p0=[0, (x_coords[-1]-x_coords[0])/num_points, x_coords[0]])
            ax, bx, cx = popt_x
        except:
            # Fallback to linear fit if quadratic fails
            z = np.polyfit(x_indices, x_coords, 1)
            ax, bx, cx = 0, z[0], z[1]
            
        # Generate smooth trajectory with more points
        num_smooth_points = max(20, num_points * 2)
        smooth_indices = np.linspace(0, num_points - 1, num_smooth_points)
        
        trajectory_3d = []
        
        for i, t_idx in enumerate(smooth_indices):
            # Progress through trajectory
            t = i / (num_smooth_points - 1)
            
            # X: lateral movement (map from 2D)
            if len(trajectory_2d) > 1:
                # Smooth X using fitted curve instead of interpolation
                x_interp = self._parabolic_function(t_idx, ax, bx, cx)
                x_3d = (x_interp - width/2) / 100.0  # Normalize to court scale using actual video center
            else:
                x_3d = 0
            
            # Z: depth (forward movement on court)
            z_3d = -3 + t * 6  # Move from back (-3m) to front (+3m)
            
            # Y: height using fitted parabola
            y_fitted = self._parabolic_function(t_idx, a, b, c)
            # Map to 3D height (normalize and scale)
            y_3d = max(0, (max(y_coords) - y_fitted) / 100.0)  # Invert and scale
            y_3d = min(3.0, y_3d)  # Cap maximum height
            
            trajectory_3d.append([x_3d, y_3d, z_3d])
        
        # Ensure last point touches ground
        trajectory_3d[-1][1] = 0
        
        return trajectory_3d
    
    def _generate_camera_path_scurve(self, total_frames, zoom_duration):
        """Generate camera positions with S-curve (ease-in/ease-out) interpolation."""
        # Start: Stadium view (high and angled)
        start_pos = np.array([0, 12, -15])  # High and back
        start_pitch = 45  # Looking down at 45 degrees
        
        # End: Top-down view
        end_pos = np.array([0, 15, 0])  # Directly above court center
        end_pitch = 89.9  # Nearly straight down
        
        camera_path = []
        
        for i in range(total_frames):
            if i < zoom_duration:
                # S-curve interpolation (ease-in, ease-out)
                t = i / zoom_duration
                # Smoothstep function: 3t² - 2t³
                ease_t = 3 * t**2 - 2 * t**3
                
                pos = start_pos + (end_pos - start_pos) * ease_t
                pitch = start_pitch + (end_pitch - start_pitch) * ease_t
            else:
                # Stay at final position
                pos = end_pos
                pitch = end_pitch
            
            camera_path.append((pos, pitch))
        
        return camera_path
    
    def _render_court_floor(self, frame, court_model, camera, mode):
        """Render the court floor with broadcast green color (#238363)."""
        floor_quad = court_model.get_floor_grid(mode)
        
        # Project floor corners to 2D
        projected = []
        debug_projected = []
        for vertex in floor_quad:
            pt_2d = camera.project_point(np.array(vertex))
            if pt_2d:
                projected.append(pt_2d)
                debug_projected.append(pt_2d)
            else:
                 debug_projected.append("None")
        
        # Log first frame projection to debug black screen
        if not hasattr(self, '_logged_projection'):
            logger.info(f"DEBUG PROJECTION: Cam Pos: {camera.pos}, Pitch: {camera.pitch}")
            logger.info(f"DEBUG PROJECTION: Court Vertices: {floor_quad}")
            logger.info(f"DEBUG PROJECTION: Projected 2D: {debug_projected}")
            self._logged_projection = True
        
        if len(projected) >= 3:
            # Fill the floor polygon with broadcast green #238363
            # RGB: (35, 131, 99) -> BGR: (99, 131, 35)
            broadcast_green = (99, 131, 35)
            pts = np.array(projected, dtype=np.int32)
            cv2.fillPoly(frame, [pts], broadcast_green, cv2.LINE_AA)
        
        return frame
    
    def _render_court_lines(self, frame, court_model, camera):
        """Render white court lines."""
        for line_type, line_list in court_model.lines.items():
            for line in line_list:
                pt1_3d, pt2_3d = line
                pt1_2d = camera.project_point(np.array(pt1_3d))
                pt2_2d = camera.project_point(np.array(pt2_3d))
                
                if pt1_2d and pt2_2d:
                    cv2.line(frame, pt1_2d, pt2_2d, (255, 255, 255), 3, cv2.LINE_AA)
        
        return frame
    
    def _render_impact_effect(self, frame, impact_point_2d, trajectory_3d, camera, timer):
        """Render impact point with fixed dark gray oval contact mark and expanding rings."""
        # Use last point of trajectory as impact in 3D
        if trajectory_3d:
            impact_3d = trajectory_3d[-1]
            impact_2d = camera.project_point(np.array(impact_3d))
            
            if impact_2d:
                # Fixed dark gray oval "contact mark" that stays on the court
                # This is the key "evidence" for the viewer
                contact_color = (50, 50, 50)  # Dark gray
                cv2.ellipse(frame, impact_2d, (20, 12), 0, 0, 360, contact_color, -1, cv2.LINE_AA)
                
                # Expanding rings (only for first few frames)
                if timer < 30:
                    for i in range(3):
                        wave_progress = (timer + i * 5) / 30.0
                        if wave_progress < 1.0:
                            radius = int(20 + wave_progress * 40)
                            alpha = 1.0 - wave_progress
                            color = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
                            cv2.circle(frame, impact_2d, radius, color, 2, cv2.LINE_AA)
        
        return frame
    
    def _render_verdict_with_shadow(self, frame, decision, width, height):
        """Render the final IN/OUT verdict with drop shadow."""
        # Verdict box at bottom center
        box_width = 400
        box_height = 120
        x1 = (width - box_width) // 2
        y1 = height - box_height - 50
        x2 = x1 + box_width
        y2 = y1 + box_height
        
        # Color based on decision
        if decision == "IN":
            bg_color = (0, 180, 0)  # Green
            text_color = (255, 255, 255)
        else:
            bg_color = (0, 0, 220)  # Red
            text_color = (255, 255, 255)
        
        # Draw drop shadow first (offset by 8 pixels down and right)
        shadow_offset = 8
        shadow_color = (20, 20, 20)  # Very dark gray, semi-transparent effect
        shadow_x1, shadow_y1 = x1 + shadow_offset, y1 + shadow_offset
        shadow_x2, shadow_y2 = x2 + shadow_offset, y2 + shadow_offset
        
        # Create shadow layer
        shadow_layer = frame.copy()
        self._draw_rounded_rect(shadow_layer, (shadow_x1, shadow_y1), (shadow_x2, shadow_y2), 
                               shadow_color, -1, 15, filled=True)
        # Blur the shadow for soft effect
        shadow_blurred = cv2.GaussianBlur(shadow_layer, (15, 15), 0)
        cv2.addWeighted(shadow_blurred, 0.5, frame, 0.5, 0, frame)
        
        # Draw main verdict box on top
        self._draw_rounded_rect(frame, (x1, y1), (x2, y2), bg_color, -1, 15, filled=True)
        self._draw_rounded_rect(frame, (x1, y1), (x2, y2), (255, 255, 255), 3, 15, filled=False)
        
        # Draw text
        font = cv2.FONT_HERSHEY_TRIPLEX  # Triplex is naturally bolder
        text = decision
        font_scale = 3.0
        thickness = 5  # Reduced thickness slightly as Triplex is already bold
        
        (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
        text_x = (width - text_width) // 2
        text_y = y1 + (box_height + text_height) // 2
        
        cv2.putText(frame, text, (text_x, text_y), font, font_scale, text_color, thickness, cv2.LINE_AA)
        
        return frame
    
    def _add_branding(self, frame, width, height):
        """Add logo/branding to the frame."""
        # Add "ALiCaS" branding in corner
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = "ALiCaS"
        font_scale = 0.8
        thickness = 2
        
        cv2.putText(frame, text, (20, height - 20), font, font_scale, (200, 200, 200), thickness, cv2.LINE_AA)
        
        return frame

    def generate_spinning_card(self, decision, background_frame, fps, duration=4.0):
        """
        Yields frames for a spinning card animation overlaid on the background.
        [LEGACY METHOD - Kept for backward compatibility]
        """
        height, width = background_frame.shape[:2]
        center_x, center_y = width // 2, height // 2
        
        total_frames = int(fps * duration)
        
        # Create a darkened version of the background
        # Blur it slightly to focus on the card
        overlay = background_frame.copy()
        blurred_bg = cv2.GaussianBlur(overlay, (21, 21), 0)
        dark_bg = cv2.addWeighted(blurred_bg, 0.4, np.zeros_like(blurred_bg), 0.6, 0)
        
        # Card Dimensions
        card_h = int(height * 0.6)
        card_w_full = int(card_h * 0.7) # Aspect ratio typical of a card
        
        # Fonts
        font = cv2.FONT_HERSHEY_DUPLEX
        font_scale = min(width, height) / 500.0
        
        # Animation Physics
        # Ease-out rotation: fast start, slow stop
        target_rotations = 4.5 # End on 4.5 rotations to show the "Back" side (if Back is at 180 deg)
        # Actually:
        # 0 deg: Front
        # 180 deg: Back
        # 360 deg: Front
        # We want to end on 'Back' (decision).
        # So we need to end at 180, 540, 900, etc. (odd multiples of 180)
        # 4.5 rotations = 4.5 * 360 = 1620 (End at Front) -> Incorrect.
        # We want X.5 rotations. e.g. 2.5 rotations = 900 degrees.
        total_degrees = 5 * 180 # 2.5 rotations
        
        for i in range(total_frames):
            frame = dark_bg.copy()
            
            # Progress 0.0 to 1.0
            t = i / total_frames
            # Ease out func: 1 - (1-t)^3
            ease_t = 1 - math.pow(1 - t, 3)
            
            current_angle = ease_t * total_degrees
            
            # Determine effective width based on rotation (projection)
            # cos(0) = 1 (Full width), cos(90) = 0 (Invisible)
            cos_theta = math.cos(math.radians(current_angle))
            current_width = int(card_w_full * abs(cos_theta))
            
            # Determine side
            # Front: cos_theta > 0 (approximately, depending on phase)
            # Actually, standard cosine:
            # 0-90: +, 90-270: -, 270-360: +
            # So Positive = Front, Negative = Back
            is_front = cos_theta >= 0
            
            if current_width > 2: # Only draw if visible
                x1 = center_x - current_width // 2
                y1 = center_y - card_h // 2
                x2 = center_x + current_width // 2
                y2 = center_y + card_h // 2
                
                # Colors
                if is_front:
                    # Generic "Analyzing" side
                    bg_color = (255, 255, 255) # White card
                    text_color = (50, 50, 50)
                    perimeter_color = (200, 200, 200)
                    main_text = "ALiCaS"
                    sub_text = "JUDGING..."
                else:
                    # Decision Side
                    if decision == "IN":
                        bg_color = (0, 200, 0) # Green
                    else:
                        bg_color = (0, 0, 200) # Red
                    text_color = (255, 255, 255)
                    perimeter_color = (255, 255, 255)
                    main_text = decision
                    sub_text = ""

                # Draw Card Body
                self._draw_rounded_rect(frame, (x1, y1), (x2, y2), bg_color, -1, 20, filled=True)
                
                # Draw Border
                self._draw_rounded_rect(frame, (x1, y1), (x2, y2), perimeter_color, 4, 20, filled=False)
                
                # Draw Text (Only if not too thin to read)
                if current_width > card_w_full * 0.3:
                    # Main Text
                    (tw, th), _ = cv2.getTextSize(main_text, font, font_scale * 2, 2)
                    # Scale text horizontally to match card perspective
                    # This is a hacky way: just drawing it normally might look weird if card is thin.
                    # Ideally we wrap perspective, but for simple overlay:
                    # We usually skip text if it's very thin, or just draw it centered.
                    
                    # Let's try to center it.
                    tx = center_x - tw // 2
                    ty = center_y + th // 2
                    
                    if is_front:
                        cv2.putText(frame, main_text, (tx, ty - 20), font, font_scale * 2, text_color, 3)
                        # Subtext
                        (stw, sth), _ = cv2.getTextSize(sub_text, font, font_scale, 1)
                        stx = center_x - stw // 2
                        sty = center_y + sth + 40
                        cv2.putText(frame, sub_text, (stx, sty), font, font_scale, (100, 100, 100), 2)
                    else:
                        cv2.putText(frame, main_text, (tx, ty), font, font_scale * 3, text_color, 5)

            yield frame
