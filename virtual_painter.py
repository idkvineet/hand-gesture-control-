import cv2
import numpy as np
from hand_detector import HandDetector

class VirtualPainter:
    """
    Virtual painting application using hand gestures.
    Use index finger to draw, selection gesture to choose colors.
    """
    
    def __init__(self):
        self.detector = HandDetector(detection_confidence=0.7, max_hands=1)
        
        # Canvas setup
        self.canvas = None
        self.drawing = False
        self.prev_x, self.prev_y = 0, 0
        
        # Color palette
        self.colors = {
            'red': (0, 0, 255),
            'green': (0, 255, 0),
            'blue': (255, 0, 0),
            'yellow': (0, 255, 255),
            'white': (255, 255, 255),
            'eraser': (0, 0, 0)
        }
        
        self.current_color = self.colors['blue']
        self.brush_thickness = 10
        self.eraser_thickness = 50
        
        # Color selection boxes
        self.color_boxes = {}
        
    def setup_color_palette(self, img_width):
        """Setup color selection boxes."""
        box_width = 100
        box_height = 60
        y_pos = 20
        x_start = 50
        spacing = 120
        
        color_names = ['red', 'green', 'blue', 'yellow', 'white', 'eraser']
        
        for i, color_name in enumerate(color_names):
            x_pos = x_start + i * spacing
            self.color_boxes[color_name] = {
                'pos': (x_pos, y_pos, x_pos + box_width, y_pos + box_height),
                'color': self.colors[color_name]
            }
    
    def draw_color_palette(self, img):
        """Draw color selection palette on image."""
        for color_name, box_info in self.color_boxes.items():
            x1, y1, x2, y2 = box_info['pos']
            color = box_info['color']
            
            # Draw box
            cv2.rectangle(img, (x1, y1), (x2, y2), color, -1)
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 255, 255), 2)
            
            # Highlight current color
            if tuple(self.current_color) == tuple(color):
                cv2.rectangle(img, (x1-5, y1-5), (x2+5, y2+5), (0, 255, 0), 4)
            
            # Add label
            label = "Eraser" if color_name == 'eraser' else color_name.capitalize()
            cv2.putText(img, label, (x1 + 5, y1 + 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return img
    
    def check_color_selection(self, x, y):
        """Check if fingertip is over a color box."""
        for color_name, box_info in self.color_boxes.items():
            x1, y1, x2, y2 = box_info['pos']
            if x1 < x < x2 and y1 < y < y2:
                self.current_color = box_info['color']
                return True
        return False
    
    def draw_instructions(self, img):
        """Draw instructions on screen."""
        h, w, _ = img.shape
        
        # Instructions box
        overlay = img.copy()
        cv2.rectangle(overlay, (w - 300, h - 150), (w - 10, h - 10), 
                     (50, 50, 50), -1)
        cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)
        
        instructions = [
            "Index up: Draw",
            "Index+Middle up: Selection",
            "Fist: Stop drawing",
            "'c': Clear canvas",
            "'q': Quit"
        ]
        
        for i, text in enumerate(instructions):
            cv2.putText(img, text, (w - 290, h - 130 + i * 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return img
    
    def process_frame(self, img):
        """Process frame and handle drawing logic."""
        if self.canvas is None:
            self.canvas = np.zeros_like(img)
        
        # Setup palette if not done
        if not self.color_boxes:
            self.setup_color_palette(img.shape[1])
        
        # Detect hand
        img = self.detector.find_hands(img, draw=True)
        landmark_list = self.detector.find_position(img, draw=False)
        
        if len(landmark_list) != 0:
            # Get fingertip positions
            x_index, y_index = landmark_list[8][1], landmark_list[8][2]  # Index finger
            x_middle, y_middle = landmark_list[12][1], landmark_list[12][2]  # Middle finger
            
            # Check finger status
            fingers = self.detector.fingers_up(landmark_list)
            
            # Selection mode: Index and Middle fingers up
            if fingers[1] and fingers[2]:
                self.drawing = False
                cv2.circle(img, (x_index, y_index), 15, (0, 255, 255), cv2.FILLED)
                
                # Check color selection
                self.check_color_selection(x_index, y_index)
                
                self.prev_x, self.prev_y = 0, 0
            
            # Drawing mode: Only Index finger up
            elif fingers[1] and not fingers[2]:
                cv2.circle(img, (x_index, y_index), 15, self.current_color, cv2.FILLED)
                
                # Don't draw on color palette area
                if y_index > 100:
                    if self.prev_x == 0 and self.prev_y == 0:
                        self.prev_x, self.prev_y = x_index, y_index
                    
                    # Determine thickness
                    thickness = self.eraser_thickness if tuple(self.current_color) == (0, 0, 0) else self.brush_thickness
                    
                    # Draw line
                    cv2.line(self.canvas, (self.prev_x, self.prev_y), 
                            (x_index, y_index), self.current_color, thickness)
                    cv2.line(img, (self.prev_x, self.prev_y), 
                            (x_index, y_index), self.current_color, thickness)
                    
                    self.prev_x, self.prev_y = x_index, y_index
                    self.drawing = True
                else:
                    self.prev_x, self.prev_y = 0, 0
            
            # Stop drawing
            else:
                self.drawing = False
                self.prev_x, self.prev_y = 0, 0
        
        # Merge canvas with camera feed
        img_gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
        _, img_inv = cv2.threshold(img_gray, 50, 255, cv2.THRESH_BINARY_INV)
        img_inv = cv2.cvtColor(img_inv, cv2.COLOR_GRAY2BGR)
        img = cv2.bitwise_and(img, img_inv)
        img = cv2.bitwise_or(img, self.canvas)
        
        # Draw UI elements
        img = self.draw_color_palette(img)
        img = self.draw_instructions(img)
        
        return img
    
    def clear_canvas(self):
        """Clear the canvas."""
        if self.canvas is not None:
            self.canvas.fill(0)

def main():
    """
    Main virtual painter application.
    """
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)
    cap.set(4, 720)
    
    painter = VirtualPainter()
    
    print("\n=== Virtual Painter ===")
    print("Instructions:")
    print("- Index finger up: Draw on canvas")
    print("- Index + Middle finger up: Select colors")
    print("- Fist: Stop drawing")
    print("- Press 'c': Clear canvas")
    print("- Press 'q': Quit\n")
    
    while True:
        success, img = cap.read()
        if not success:
            break
        
        img = cv2.flip(img, 1)
        
        # Process frame
        img = painter.process_frame(img)
        
        # Display
        cv2.imshow("Virtual Painter", img)
        
        # Handle keyboard input
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c'):
            painter.clear_canvas()
            print("Canvas cleared")
    
    cap.release()
    cv2.destroyAllWindows()
    print("Virtual Painter closed")

if __name__ == "__main__":
    main()