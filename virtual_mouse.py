import cv2
import numpy as np
from hand_detector import HandDetector
import math
import time

# Try importing pyautogui
try:
    import pyautogui
    # PyAutoGUI settings for smooth operation
    pyautogui.FAILSAFE = False  # Disable failsafe (moving mouse to corner won't stop script)
    pyautogui.PAUSE = 0  # Remove pause between PyAutoGUI calls for smooth movement
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("Warning: PyAutoGUI not installed. Mouse control will not work.")
    print("Install with: pip install pyautogui")

class VirtualMouse:
    """
    Control mouse cursor using hand gestures.
    - Index finger up: Move cursor
    - Index + Middle pinch: Left click
    - All fingers up: Right click
    - Fist: Scroll mode
    """
    
    def __init__(self):
        self.detector = HandDetector(detection_confidence=0.8, max_hands=1)
        
        # Screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()
        
        # Camera frame dimensions (will be set in main loop)
        self.frame_width = 640
        self.frame_height = 480
        
        # Smoothing for cursor movement
        self.smoothing = 7
        self.prev_x, self.prev_y = 0, 0
        self.curr_x, self.curr_y = 0, 0
        
        # Click detection
        self.click_threshold = 40  # Distance threshold for click detection
        self.click_cooldown = 0.3  # Seconds between clicks
        self.last_click_time = 0
        
        # Scroll mode
        self.scroll_mode = False
        self.scroll_start_y = 0
        
        # Active zone (area of frame to use for mouse control)
        self.active_zone_margin = 100  # pixels from edge
        
        # Movement sensitivity
        self.sensitivity_x = 2.5  # Higher = more sensitive horizontal movement
        self.sensitivity_y = 2.5  # Higher = more sensitive vertical movement
        
        print(f"✓ Virtual Mouse initialized")
        print(f"  Screen resolution: {self.screen_width}x{self.screen_height}")
    
    def get_cursor_position(self, index_finger_pos):
        """
        Convert finger position to screen coordinates with smoothing.
        
        Args:
            index_finger_pos: (x, y) position of index finger tip
            
        Returns:
            (x, y) screen coordinates for cursor
        """
        x, y = index_finger_pos
        
        # Map finger position to screen coordinates
        # Flip x-axis for natural mirror movement
        x = np.interp(x, [self.active_zone_margin, self.frame_width - self.active_zone_margin], 
                     [0, self.screen_width])
        y = np.interp(y, [self.active_zone_margin, self.frame_height - self.active_zone_margin], 
                     [0, self.screen_height])
        
        # Apply sensitivity
        x = x * self.sensitivity_x
        y = y * self.sensitivity_y
        
        # Clamp to screen bounds
        x = np.clip(x, 0, self.screen_width - 1)
        y = np.clip(y, 0, self.screen_height - 1)
        
        # Smooth the movement
        self.curr_x = self.prev_x + (x - self.prev_x) / self.smoothing
        self.curr_y = self.prev_y + (y - self.prev_y) / self.smoothing
        
        self.prev_x, self.prev_y = self.curr_x, self.curr_y
        
        return int(self.curr_x), int(self.curr_y)
    
    def detect_left_click(self, landmark_list):
        """
        Detect left click gesture (thumb and index finger pinch).
        
        Args:
            landmark_list: Hand landmarks
            
        Returns:
            True if click detected, False otherwise
        """
        if len(landmark_list) < 21:
            return False
        
        # Get thumb tip (4) and index tip (8)
        thumb_tip = landmark_list[4]
        index_tip = landmark_list[8]
        
        # Calculate distance
        distance = math.hypot(thumb_tip[1] - index_tip[1], thumb_tip[2] - index_tip[2])
        
        # Check cooldown
        current_time = time.time()
        if current_time - self.last_click_time < self.click_cooldown:
            return False
        
        # Detect click
        if distance < self.click_threshold:
            self.last_click_time = current_time
            return True
        
        return False
    
    def detect_right_click(self, fingers):
        """
        Detect right click gesture (all fingers up).
        
        Args:
            fingers: List of finger states
            
        Returns:
            True if right click detected
        """
        if len(fingers) != 5:
            return False
        
        # All fingers up
        return all(fingers)
    
    def detect_scroll_mode(self, fingers):
        """
        Detect scroll mode (fist - all fingers down).
        
        Args:
            fingers: List of finger states
            
        Returns:
            True if scroll mode active
        """
        if len(fingers) != 5:
            return False
        
        # All fingers down (fist)
        return not any(fingers)
    
    def perform_scroll(self, current_y):
        """
        Perform scrolling based on hand movement.
        
        Args:
            current_y: Current y position of hand
        """
        if self.scroll_start_y == 0:
            self.scroll_start_y = current_y
            return
        
        # Calculate scroll amount
        delta_y = self.scroll_start_y - current_y
        
        if abs(delta_y) > 20:  # Minimum movement to scroll
            scroll_amount = int(delta_y / 10)
            pyautogui.scroll(scroll_amount)
            self.scroll_start_y = current_y
    
    def draw_ui(self, img, landmark_list, mode, cursor_pos=None):
        """
        Draw UI elements and visual feedback.
        
        Args:
            img: Input image
            landmark_list: Hand landmarks
            mode: Current mode string
            cursor_pos: Cursor position tuple
        """
        h, w, _ = img.shape
        
        # Draw active zone rectangle
        cv2.rectangle(img, 
                     (self.active_zone_margin, self.active_zone_margin),
                     (w - self.active_zone_margin, h - self.active_zone_margin),
                     (0, 255, 0), 2)
        
        # Draw control panel
        overlay = img.copy()
        cv2.rectangle(overlay, (10, 10), (w - 10, 180), (50, 50, 50), -1)
        cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)
        
        # Title
        cv2.putText(img, "Virtual Mouse Control", (20, 45),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        # Current mode
        mode_color = (0, 255, 0) if mode != "No Hand" else (0, 0, 255)
        cv2.putText(img, f"Mode: {mode}", (20, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, mode_color, 2)
        
        # Cursor position
        if cursor_pos:
            cv2.putText(img, f"Cursor: ({cursor_pos[0]}, {cursor_pos[1]})", (20, 110),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Screen info
        cv2.putText(img, f"Screen: {self.screen_width}x{self.screen_height}", (20, 135),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Smoothing info
        cv2.putText(img, f"Smoothing: {self.smoothing}", (20, 160),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Instructions panel
        instructions_y = h - 200
        overlay2 = img.copy()
        cv2.rectangle(overlay2, (10, instructions_y), (500, h - 10), (50, 50, 50), -1)
        cv2.addWeighted(overlay2, 0.7, img, 0.3, 0, img)
        
        instructions = [
            "GESTURES:",
            "Index finger up: Move cursor",
            "Thumb + Index pinch: Left click",
            "All fingers up: Right click",
            "Fist: Scroll mode",
            "Press 'q' to quit"
        ]
        
        for i, text in enumerate(instructions):
            color = (0, 255, 255) if i == 0 else (255, 255, 255)
            thickness = 2 if i == 0 else 1
            cv2.putText(img, text, (20, instructions_y + 30 + i * 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness)
        
        # Draw finger markers if hand detected
        if len(landmark_list) > 0:
            # Thumb (4) - Red
            cv2.circle(img, (landmark_list[4][1], landmark_list[4][2]), 
                      10, (0, 0, 255), cv2.FILLED)
            # Index (8) - Green
            cv2.circle(img, (landmark_list[8][1], landmark_list[8][2]), 
                      10, (0, 255, 0), cv2.FILLED)
            # Middle (12) - Blue
            cv2.circle(img, (landmark_list[12][1], landmark_list[12][2]), 
                      10, (255, 0, 0), cv2.FILLED)
            
            # Draw line between thumb and index for click detection
            distance = math.hypot(
                landmark_list[4][1] - landmark_list[8][1],
                landmark_list[4][2] - landmark_list[8][2]
            )
            color = (0, 255, 0) if distance < self.click_threshold else (255, 0, 255)
            cv2.line(img, 
                    (landmark_list[4][1], landmark_list[4][2]),
                    (landmark_list[8][1], landmark_list[8][2]),
                    color, 3)
            
            # Show click distance
            mid_x = (landmark_list[4][1] + landmark_list[8][1]) // 2
            mid_y = (landmark_list[4][2] + landmark_list[8][2]) // 2
            cv2.putText(img, f"{int(distance)}px", (mid_x, mid_y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return img

def main():
    """
    Main virtual mouse application.
    """
    # Initialize
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)
    cap.set(4, 720)
    
    # Get actual frame dimensions
    ret, frame = cap.read()
    if ret:
        frame_h, frame_w, _ = frame.shape
    else:
        frame_w, frame_h = 640, 480
    
    mouse = VirtualMouse()
    mouse.frame_width = frame_w
    mouse.frame_height = frame_h
    
    print("\n" + "="*70)
    print("              VIRTUAL MOUSE CONTROL WITH HAND GESTURES")
    print("="*70)
    print("\nGestures:")
    print("  👆 Index finger up         → Move cursor")
    print("  🤏 Thumb + Index pinch     → Left click")
    print("  ✋ All fingers up          → Right click")
    print("  ✊ Fist (all fingers down) → Scroll mode")
    print("\nTips:")
    print("  • Keep hand within the green rectangle")
    print("  • Move slowly for precise control")
    print("  • Hold gesture for 0.3s for clicks")
    print("  • Press 'q' to quit")
    print("="*70 + "\n")
    
    input("Press ENTER to start...")
    print("\n✓ Virtual mouse active!\n")
    
    while True:
        success, img = cap.read()
        if not success:
            print("Failed to grab frame")
            break
        
        img = cv2.flip(img, 1)
        
        # Detect hand
        img = mouse.detector.find_hands(img, draw=True)
        landmark_list = mouse.detector.find_position(img, draw=False)
        
        mode = "No Hand"
        cursor_pos = None
        
        if len(landmark_list) != 0:
            fingers = mouse.detector.fingers_up(landmark_list)
            
            # Get index finger tip position (landmark 8)
            index_tip = (landmark_list[8][1], landmark_list[8][2])
            
            # Check different gestures
            
            # Scroll mode (fist)
            if mouse.detect_scroll_mode(fingers):
                mode = "Scroll Mode"
                mouse.scroll_mode = True
                mouse.perform_scroll(index_tip[1])
            
            # Right click (all fingers up)
            elif mouse.detect_right_click(fingers):
                mode = "Right Click"
                mouse.scroll_mode = False
                mouse.scroll_start_y = 0
                
                current_time = time.time()
                if current_time - mouse.last_click_time > mouse.click_cooldown:
                    pyautogui.rightClick()
                    mouse.last_click_time = current_time
                    print("  → Right click!")
            
            # Move cursor (index finger up)
            elif fingers[1]:  # Index finger is up
                mode = "Moving Cursor"
                mouse.scroll_mode = False
                mouse.scroll_start_y = 0
                
                # Get cursor position
                cursor_pos = mouse.get_cursor_position(index_tip)
                
                # Move mouse
                pyautogui.moveTo(cursor_pos[0], cursor_pos[1])
                
                # Check for left click (thumb-index pinch)
                if mouse.detect_left_click(landmark_list):
                    pyautogui.click()
                    mode = "Left Click"
                    print("  → Left click!")
            
            else:
                mode = "Idle"
                mouse.scroll_mode = False
                mouse.scroll_start_y = 0
        
        else:
            mouse.scroll_mode = False
            mouse.scroll_start_y = 0
        
        # Draw UI
        img = mouse.draw_ui(img, landmark_list, mode, cursor_pos)
        
        # Display
        cv2.imshow("Virtual Mouse Control", img)
        
        # Quit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("\n✓ Virtual mouse closed")

if __name__ == "__main__":
    main()
