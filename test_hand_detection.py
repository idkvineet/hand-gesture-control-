import cv2
from hand_detector import HandDetector

def main():
    """
    Basic hand detection test.
    Shows webcam feed with hand landmarks and finger count.
    Press 'q' to quit.
    """
    
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)  # Width
    cap.set(4, 720)   # Height
    
    # Initialize hand detector
    detector = HandDetector(detection_confidence=0.7, max_hands=2)
    
    print("Hand Detection Test Started")
    print("Press 'q' to quit")
    
    while True:
        success, img = cap.read()
        if not success:
            print("Failed to grab frame")
            break
        
        # Detect hands
        img = detector.find_hands(img)
        landmark_list = detector.find_position(img, draw=False)
        
        # If hand detected, count fingers
        if len(landmark_list) != 0:
            fingers = detector.fingers_up(landmark_list)
            total_fingers = fingers.count(1)
            
            # Display finger count
            cv2.putText(img, f'Fingers: {total_fingers}', (50, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
            
            # Display individual finger status
            finger_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
            for i, (name, status) in enumerate(zip(finger_names, fingers)):
                color = (0, 255, 0) if status else (0, 0, 255)
                cv2.putText(img, f'{name}: {"UP" if status else "DOWN"}', 
                           (50, 180 + i*40), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, color, 2)
        
        # Display frame
        cv2.imshow("Hand Detection Test", img)
        
        # Quit on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print("Test ended")

if __name__ == "__main__":
    main()