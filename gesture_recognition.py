import cv2
import numpy as np
from hand_detector import HandDetector

class GestureRecognizer:
    """
    Recognizes common hand gestures using hand landmarks.
    """
    
    def __init__(self):
        self.detector = HandDetector(detection_confidence=0.7, max_hands=2)
        self.gesture_history = []
        self.history_length = 5  # Smooth gesture detection
        
    def recognize_gesture(self, landmark_list):
        """
        Recognize gesture from hand landmarks.
        
        Returns:
            String describing the detected gesture
        """
        if len(landmark_list) == 0:
            return "No Hand"
        
        fingers = self.detector.fingers_up(landmark_list)
        total_fingers = fingers.count(1)
        
        # Thumb, Index, Middle, Ring, Pinky
        thumb, index, middle, ring, pinky = fingers
        
        # Peace/Victory Sign
        if index and middle and not ring and not pinky and not thumb:
            return "Peace Sign"
        
        # Thumbs Up
        if thumb and not index and not middle and not ring and not pinky:
            return "Thumbs Up"
        
        # Thumbs Down (thumb down is tricky, approximate by checking position)
        if not thumb and not index and not middle and not ring and not pinky:
            if landmark_list[4][2] > landmark_list[3][2]:  # Thumb tip below IP joint
                return "Thumbs Down"
        
        # OK Sign (thumb and index forming circle)
        if thumb and index:
            # Calculate distance between thumb tip and index tip
            distance = self._calculate_distance(
                landmark_list[4], landmark_list[8]
            )
            if distance < 40:  # Close together
                return "OK Sign"
        
        # Rock Sign (index and pinky up)
        if index and pinky and not middle and not ring:
            return "Rock Sign"
        
        # Fist (all fingers down)
        if total_fingers == 0:
            return "Fist"
        
        # Open Palm (all fingers up)
        if total_fingers == 5:
            return "Open Palm"
        
        # Pointing (only index up)
        if index and not middle and not ring and not pinky and not thumb:
            return "Pointing"
        
        # Three Fingers
        if index and middle and ring and not pinky and not thumb:
            return "Three Fingers"
        
        # Four Fingers
        if index and middle and ring and pinky and not thumb:
            return "Four Fingers"
        
        # Call Me (thumb and pinky up)
        if thumb and pinky and not index and not middle and not ring:
            return "Call Me"
        
        # Finger Gun (thumb and index up)
        if thumb and index and not middle and not ring and not pinky:
            return "Finger Gun"
        
        # Default: just count fingers
        return f"{total_fingers} Fingers Up"
    
    def _calculate_distance(self, point1, point2):
        """Calculate Euclidean distance between two points."""
        return np.sqrt((point1[1] - point2[1])**2 + (point1[2] - point2[2])**2)
    
    def smooth_gesture(self, current_gesture):
        """
        Smooth gesture detection to avoid flickering.
        
        Args:
            current_gesture: Currently detected gesture
            
        Returns:
            Smoothed gesture (most common in recent history)
        """
        self.gesture_history.append(current_gesture)
        
        # Keep history limited
        if len(self.gesture_history) > self.history_length:
            self.gesture_history.pop(0)
        
        # Return most common gesture in history
        if len(self.gesture_history) > 0:
            return max(set(self.gesture_history), key=self.gesture_history.count)
        
        return current_gesture
    
    def draw_gesture_info(self, img, gesture, landmark_list):
        """
        Draw gesture information and visual feedback on image.
        
        Args:
            img: Input image
            gesture: Detected gesture name
            landmark_list: Hand landmarks
        """
        h, w, _ = img.shape
        
        # Create semi-transparent overlay for info box
        overlay = img.copy()
        cv2.rectangle(overlay, (10, 10), (500, 150), (50, 50, 50), -1)
        cv2.addWeighted(overlay, 0.6, img, 0.4, 0, img)
        
        # Display gesture name
        cv2.putText(img, f"Gesture: {gesture}", (20, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)
        
        # Display finger status if hand detected
        if len(landmark_list) > 0:
            fingers = self.detector.fingers_up(landmark_list)
            finger_names = ['T', 'I', 'M', 'R', 'P']
            
            # Draw finger status indicators
            for i, (name, status) in enumerate(zip(finger_names, fingers)):
                x = 20 + i * 90
                color = (0, 255, 0) if status else (0, 0, 255)
                cv2.circle(img, (x + 20, 110), 15, color, -1)
                cv2.putText(img, name, (x + 10, 125), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # Add instructions
        cv2.putText(img, "Press 'q' to quit", (w - 300, h - 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return img

def main():
    """
    Main gesture recognition application.
    """
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)  # Width
    cap.set(4, 720)   # Height
    
    # Initialize gesture recognizer
    recognizer = GestureRecognizer()
    
    print("Gesture Recognition Started")
    print("Supported Gestures:")
    print("- Peace Sign, Thumbs Up, Thumbs Down")
    print("- OK Sign, Rock Sign, Fist, Open Palm")
    print("- Pointing, Three/Four Fingers, Call Me, Finger Gun")
    print("\nPress 'q' to quit\n")
    
    while True:
        success, img = cap.read()
        if not success:
            print("Failed to grab frame")
            break
        
        # Flip image for mirror effect
        img = cv2.flip(img, 1)
        
        # Detect hands
        img = recognizer.detector.find_hands(img)
        landmark_list = recognizer.detector.find_position(img, draw=False)
        
        # Recognize gesture
        gesture = recognizer.recognize_gesture(landmark_list)
        gesture = recognizer.smooth_gesture(gesture)
        
        # Draw info on image
        img = recognizer.draw_gesture_info(img, gesture, landmark_list)
        
        # Display
        cv2.imshow("Hand Gesture Recognition", img)
        
        # Quit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print("Application closed")

if __name__ == "__main__":
    main()