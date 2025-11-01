import cv2
import mediapipe as mp
import math

class HandDetector:
    """
    Hand detection class using MediaPipe.
    Detects hands and provides hand landmarks with helper methods.
    """
    
    def __init__(self, mode=False, max_hands=2, detection_confidence=0.5, tracking_confidence=0.5):
        """
        Initialize hand detector.
        
        Args:
            mode: Static image mode (False for video stream)
            max_hands: Maximum number of hands to detect
            detection_confidence: Minimum confidence for detection
            tracking_confidence: Minimum confidence for tracking
        """
        self.mode = mode
        self.max_hands = max_hands
        self.detection_confidence = detection_confidence
        self.tracking_confidence = tracking_confidence
        
        # Initialize MediaPipe hands module
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.max_hands,
            min_detection_confidence=self.detection_confidence,
            min_tracking_confidence=self.tracking_confidence
        )
        self.mp_draw = mp.solutions.drawing_utils
        
    def find_hands(self, img, draw=True):
        """
        Detect hands in the image.
        
        Args:
            img: Input image (BGR format from OpenCV)
            draw: Whether to draw hand landmarks on image
            
        Returns:
            Image with drawings (if draw=True)
        """
        # Convert BGR to RGB for MediaPipe
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)
        
        # Draw hand landmarks if hands detected
        if self.results.multi_hand_landmarks:
            for hand_landmarks in self.results.multi_hand_landmarks:
                if draw:
                    self.mp_draw.draw_landmarks(
                        img, 
                        hand_landmarks, 
                        self.mp_hands.HAND_CONNECTIONS
                    )
        
        return img
    
    def find_position(self, img, hand_no=0, draw=True):
        """
        Get positions of hand landmarks.
        
        Args:
            img: Input image
            hand_no: Which hand to get landmarks from (0 for first hand)
            draw: Whether to draw circles on landmarks
            
        Returns:
            List of landmarks [id, x, y] where x, y are pixel coordinates
        """
        self.landmark_list = []
        
        if self.results.multi_hand_landmarks:
            if hand_no < len(self.results.multi_hand_landmarks):
                hand = self.results.multi_hand_landmarks[hand_no]
                
                for id, landmark in enumerate(hand.landmark):
                    # Convert normalized coordinates to pixel coordinates
                    h, w, c = img.shape
                    cx, cy = int(landmark.x * w), int(landmark.y * h)
                    self.landmark_list.append([id, cx, cy])
                    
                    if draw:
                        cv2.circle(img, (cx, cy), 7, (255, 0, 255), cv2.FILLED)
        
        return self.landmark_list
    
    def fingers_up(self, landmark_list):
        """
        Check which fingers are up.
        
        Args:
            landmark_list: List of hand landmarks
            
        Returns:
            List of 5 binary values [thumb, index, middle, ring, pinky]
            1 = finger up, 0 = finger down
        """
        fingers = []
        
        if len(landmark_list) == 0:
            return fingers
        
        # Thumb (special case - check horizontal position)
        # Landmark 4 is thumb tip, 3 is thumb IP joint
        if landmark_list[4][1] < landmark_list[3][1]:  # Left hand
            fingers.append(1)
        else:
            fingers.append(0)
        
        # Other fingers (check vertical position)
        # Compare fingertip with PIP joint (2 landmarks below)
        tip_ids = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky tips
        
        for tip_id in tip_ids:
            if landmark_list[tip_id][2] < landmark_list[tip_id - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        
        return fingers
    
    def find_distance(self, p1, p2, img, draw=True):
        """
        Find distance between two landmarks.
        
        Args:
            p1: First landmark ID
            p2: Second landmark ID
            img: Input image
            draw: Whether to draw line and circles
            
        Returns:
            Distance in pixels, image, [x1, y1, x2, y2, cx, cy]
        """
        if len(self.landmark_list) < max(p1, p2) + 1:
            return 0, img, []
        
        x1, y1 = self.landmark_list[p1][1], self.landmark_list[p1][2]
        x2, y2 = self.landmark_list[p2][1], self.landmark_list[p2][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        
        if draw:
            cv2.circle(img, (x1, y1), 10, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 10, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.circle(img, (cx, cy), 8, (255, 0, 255), cv2.FILLED)
        
        length = math.hypot(x2 - x1, y2 - y1)
        
        return length, img, [x1, y1, x2, y2, cx, cy]