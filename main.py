"""
Hand Gesture Recognition System - Main Menu
============================================
This is the central hub for all hand gesture recognition applications.
Choose from various interactive features powered by MediaPipe and OpenCV.
"""

import sys
import os

def clear_screen():
    """Clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """Print application banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║         HAND GESTURE RECOGNITION SYSTEM v1.0                  ║
    ║              Powered by MediaPipe & OpenCV                    ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_menu():
    """Display main menu."""
    print("\n" + "="*65)
    print("                        MAIN MENU")
    print("="*65 + "\n")
    
    menu_items = [
        ("1", "Basic Hand Detection Test", 
         "Test webcam and see real-time hand tracking with finger counting"),
        
        ("2", "Gesture Recognition System", 
         "Recognize 10+ hand gestures (Peace, Thumbs Up, Rock, etc.)"),
        
        ("3", "Volume Control", 
         "Control system volume using pinch gesture (thumb + index)"),
        
        ("4", "Virtual Mouse Control", 
         "Control mouse cursor with hand gestures (move, click, scroll)"),
        
        ("5", "Virtual Painter", 
         "Draw in the air with your finger! Choose colors and create art"),
        
        ("6", "View Documentation", 
         "Learn about gestures, controls, and how to use each feature"),
        
        ("0", "Exit", 
         "Close the application")
    ]
    
    for num, title, desc in menu_items:
        print(f"  [{num}] {title}")
        print(f"      → {desc}\n")
    
    print("="*65)

def show_documentation():
    """Display detailed documentation."""
    clear_screen()
    print_banner()
    print("\n" + "="*65)
    print("                      DOCUMENTATION")
    print("="*65 + "\n")
    
    docs = """
📋 BASIC HAND DETECTION TEST
   • Shows live webcam feed with hand landmarks
   • Displays finger count (0-5)
   • Shows individual finger status (Up/Down)
   • Controls: Press 'q' to quit

🤚 GESTURE RECOGNITION SYSTEM
   Supported Gestures:
   • Peace Sign      - Index + Middle fingers up
   • Thumbs Up       - Only thumb up
   • Thumbs Down     - All fingers down (fist variation)
   • OK Sign         - Thumb + Index forming circle
   • Rock Sign       - Index + Pinky up
   • Fist            - All fingers closed
   • Open Palm       - All fingers extended
   • Pointing        - Only index finger up
   • Three Fingers   - Index + Middle + Ring up
   • Four Fingers    - All except thumb
   • Call Me         - Thumb + Pinky up
   • Finger Gun      - Thumb + Index up
   
   Controls: Press 'q' to quit

🔊 VOLUME CONTROL
   • Use pinch gesture (thumb and index finger)
   • Move fingers closer = Lower volume
   • Move fingers apart = Higher volume
   • Visual feedback with volume bar
   • Note: Requires 'pycaw' package on Windows
   
   Controls: Press 'q' to quit

🖱️ VIRTUAL MOUSE CONTROL
   Gestures:
   • Index finger up           - Move cursor
   • Thumb + Index pinch       - Left click
   • All fingers up            - Right click
   • Fist (all fingers down)   - Scroll mode
   
   Features:
   • Smooth cursor movement with position tracking
   • Click cooldown to prevent accidental double clicks
   • Active zone indicator (green rectangle)
   • Real-time cursor position display
   
   Note: Requires 'pyautogui' package
   
   Controls: Press 'q' to quit

🎨 VIRTUAL PAINTER
   Gestures:
   • Index finger up           - Draw on canvas
   • Index + Middle fingers up - Selection mode (choose colors)
   • Fist                      - Stop drawing
   
   Available Colors:
   • Red, Green, Blue, Yellow, White, Eraser
   
   Controls:
   • Press 'c' to clear canvas
   • Press 'q' to quit

💡 TIPS FOR BEST RESULTS:
   1. Ensure good lighting conditions
   2. Keep hand within frame
   3. Maintain contrast between hand and background
   4. Position yourself 1-2 feet from camera
   5. Make gestures clearly and hold for 1 second

⚙️ SYSTEM REQUIREMENTS:
   • Python 3.7+
   • Webcam/Camera
   • Required packages: opencv-python, mediapipe, numpy, pyautogui
   • Optional: pycaw (for volume control on Windows)

📦 INSTALLATION:
   pip install opencv-python mediapipe numpy pyautogui
   pip install pycaw  # For volume control (Windows only)
"""
    
    print(docs)
    print("="*65)
    input("\nPress ENTER to return to main menu...")

def run_basic_test():
    """Run basic hand detection test."""
    try:
        import cv2
        from hand_detector import HandDetector
        
        clear_screen()
        print_banner()
        print("\n🔍 Starting Basic Hand Detection Test...")
        print("Press 'q' to return to main menu\n")
        input("Press ENTER to start...")
        
        # Initialize webcam
        cap = cv2.VideoCapture(0)
        cap.set(3, 1280)
        cap.set(4, 720)
        
        # Initialize hand detector
        detector = HandDetector(detection_confidence=0.7, max_hands=2)
        
        print("\n✓ Camera initialized")
        print("✓ Hand detector ready")
        print("\nShowing camera feed...\n")
        
        while True:
            success, img = cap.read()
            if not success:
                print("❌ Failed to grab frame")
                break
            
            img = cv2.flip(img, 1)
            
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
        
        cap.release()
        cv2.destroyAllWindows()
        print("\n✓ Test completed successfully!")
        
    except ImportError as e:
        print(f"\n❌ Error: Missing required module - {e}")
        print("Please ensure 'hand_detector.py' is in the same directory")
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
    
    input("\nPress ENTER to return to main menu...")

def run_gesture_recognition():
    """Run gesture recognition system."""
    try:
        import cv2
        import numpy as np
        from hand_detector import HandDetector
        
        clear_screen()
        print_banner()
        print("\n🤚 Starting Gesture Recognition System...")
        print("Press 'q' to return to main menu\n")
        input("Press ENTER to start...")
        
        # Import GestureRecognizer class
        from gesture_recognition import GestureRecognizer
        
        cap = cv2.VideoCapture(0)
        cap.set(3, 1280)
        cap.set(4, 720)
        
        recognizer = GestureRecognizer()
        
        print("\n✓ Camera initialized")
        print("✓ Gesture recognizer ready")
        print("\nShowing camera feed...\n")
        
        while True:
            success, img = cap.read()
            if not success:
                break
            
            img = cv2.flip(img, 1)
            img = recognizer.detector.find_hands(img)
            landmark_list = recognizer.detector.find_position(img, draw=False)
            
            gesture = recognizer.recognize_gesture(landmark_list)
            gesture = recognizer.smooth_gesture(gesture)
            
            img = recognizer.draw_gesture_info(img, gesture, landmark_list)
            
            cv2.imshow("Hand Gesture Recognition", img)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        print("\n✓ Gesture recognition closed successfully!")
        
    except ImportError as e:
        print(f"\n❌ Error: Missing required module - {e}")
        print("Please ensure 'gesture_recognition.py' is in the same directory")
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
    
    input("\nPress ENTER to return to main menu...")

def run_volume_control():
    """Run volume control application."""
    try:
        import cv2
        import numpy as np
        from hand_detector import HandDetector
        import math
        
        clear_screen()
        print_banner()
        print("\n🔊 Starting Volume Control...")
        print("Press 'q' to return to main menu\n")
        
        input("Press ENTER to start...")
        
        from volume_control import VolumeController
        
        cap = cv2.VideoCapture(0)
        cap.set(3, 1280)
        cap.set(4, 720)
        
        controller = VolumeController()
        
        print("\n✓ Camera initialized")
        print("✓ Volume controller ready")
        print("\nShowing camera feed...\n")
        
        while True:
            success, img = cap.read()
            if not success:
                break
            
            img = cv2.flip(img, 1)
            img = controller.detector.find_hands(img)
            landmark_list = controller.detector.find_position(img, draw=False)
            
            vol_percentage = 0
            distance = 0
            
            if len(landmark_list) != 0:
                x1, y1 = landmark_list[4][1], landmark_list[4][2]
                x2, y2 = landmark_list[8][1], landmark_list[8][2]
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                
                cv2.circle(img, (x1, y1), 12, (255, 0, 255), cv2.FILLED)
                cv2.circle(img, (x2, y2), 12, (255, 0, 255), cv2.FILLED)
                cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
                
                distance = math.hypot(x2 - x1, y2 - y1)
                
                if distance < 50:
                    cv2.circle(img, (cx, cy), 12, (0, 255, 0), cv2.FILLED)
                else:
                    cv2.circle(img, (cx, cy), 12, (255, 0, 255), cv2.FILLED)
                
                vol_percentage = controller.set_volume(distance)
            
            img = controller.draw_volume_bar(img, vol_percentage, distance)
            cv2.imshow("Volume Control - Hand Gestures", img)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        print("\n✓ Volume control closed successfully!")
        
    except ImportError as e:
        print(f"\n❌ Error: Missing required module - {e}")
        print("Please ensure 'volume_control.py' is in the same directory")
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
    
    input("\nPress ENTER to return to main menu...")

def run_virtual_mouse():
    """Run virtual mouse control application."""
    try:
        # Check for pyautogui first
        try:
            import pyautogui
        except ImportError:
            clear_screen()
            print_banner()
            print("\n❌ Error: PyAutoGUI not installed")
            print("\nPyAutoGUI is required for virtual mouse functionality.")
            print("\nTo install, run:")
            print("  pip install pyautogui")
            print("\nFor Linux users, you may also need:")
            print("  sudo apt-get install python3-tk python3-dev")
            input("\nPress ENTER to return to main menu...")
            return
        
        clear_screen()
        print_banner()
        print("\n🖱️ Starting Virtual Mouse Control...")
        print("Press 'q' to return to main menu\n")
        
        # Import the virtual_mouse module
        try:
            import virtual_mouse
            # Reload module to get fresh instance
            import importlib
            importlib.reload(virtual_mouse)
        except ImportError as e:
            print(f"\n❌ Error: Could not import virtual_mouse.py")
            print(f"  Details: {e}")
            print("\nPlease ensure 'virtual_mouse.py' is in the same directory as main.py")
            input("\nPress ENTER to return to main menu...")
            return
        
        print("Controls:")
        print("  • Index finger up: Move cursor")
        print("  • Thumb + Index pinch: Left click")
        print("  • All fingers up: Right click")
        print("  • Fist: Scroll mode\n")
        input("Press ENTER to start...")
        
        print("\nInitializing virtual mouse...")
        
        # Run the virtual mouse main function
        virtual_mouse.main()
        
    except KeyboardInterrupt:
        print("\n\n✓ Virtual mouse interrupted by user")
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress ENTER to return to main menu...")

def run_virtual_painter():
    """Run virtual painter application."""
    try:
        import cv2
        import numpy as np
        from hand_detector import HandDetector
        
        clear_screen()
        print_banner()
        print("\n🎨 Starting Virtual Painter...")
        print("Press 'q' to return to main menu\n")
        print("Controls:")
        print("  • Index finger up: Draw")
        print("  • Index + Middle up: Select color")
        print("  • Press 'c': Clear canvas\n")
        input("Press ENTER to start...")
        
        from virtual_painter import VirtualPainter
        
        cap = cv2.VideoCapture(0)
        cap.set(3, 1280)
        cap.set(4, 720)
        
        painter = VirtualPainter()
        
        print("\n✓ Camera initialized")
        print("✓ Virtual painter ready")
        print("\nShowing camera feed...\n")
        
        while True:
            success, img = cap.read()
            if not success:
                break
            
            img = cv2.flip(img, 1)
            img = painter.process_frame(img)
            
            cv2.imshow("Virtual Painter", img)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                painter.clear_canvas()
                print("  → Canvas cleared")
        
        cap.release()
        cv2.destroyAllWindows()
        print("\n✓ Virtual painter closed successfully!")
        
    except ImportError as e:
        print(f"\n❌ Error: Missing required module - {e}")
        print("Please ensure 'virtual_painter.py' is in the same directory")
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
    
    input("\nPress ENTER to return to main menu...")

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("\nChecking dependencies...")
    
    dependencies = {
        'opencv-python': 'cv2',
        'mediapipe': 'mediapipe',
        'numpy': 'numpy',
        'pyautogui': 'pyautogui'
    }
    
    missing = []
    
    for package, module in dependencies.items():
        try:
            __import__(module)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - NOT INSTALLED")
            missing.append(package)
    
    # Check optional dependencies
    try:
        __import__('pycaw')
        print(f"  ✓ pycaw (optional - for volume control)")
    except ImportError:
        print(f"  ⚠ pycaw (optional) - Not installed. Volume control will run in simulation mode.")
    
    if missing:
        print(f"\n❌ Missing required packages: {', '.join(missing)}")
        print("\nPlease install them using:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    print("\n✓ All required dependencies are installed!")
    return True

def main():
    """Main application loop."""
    
    # Initial dependency check
    clear_screen()
    print_banner()
    
    if not check_dependencies():
        print("\n" + "="*65)
        input("\nPress ENTER to exit...")
        sys.exit(1)
    
    # Main menu loop
    while True:
        clear_screen()
        print_banner()
        print_menu()
        
        choice = input("\nEnter your choice (0-6): ").strip()
        
        if choice == '1':
            run_basic_test()
        elif choice == '2':
            run_gesture_recognition()
        elif choice == '3':
            run_volume_control()
        elif choice == '4':
            run_virtual_mouse()
        elif choice == '5':
            run_virtual_painter()
        elif choice == '6':
            show_documentation()
        elif choice == '0':
            clear_screen()
            print_banner()
            print("\n👋 Thank you for using Hand Gesture Recognition System!")
            print("   Goodbye!\n")
            sys.exit(0)
        else:
            print("\n❌ Invalid choice! Please enter a number between 0-6.")
            input("Press ENTER to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Application interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        input("Press ENTER to exit...")
        sys.exit(1)
