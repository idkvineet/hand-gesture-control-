import cv2
import numpy as np
from hand_detector import HandDetector
import math
import platform

class VolumeController:
    """
    Control system volume using hand gestures.
    Uses pinch gesture (thumb and index finger distance).
    Cross-platform support with multiple backends.
    """
    
    def __init__(self):
        self.detector = HandDetector(detection_confidence=0.75, max_hands=1)
        
        # Initialize volume control
        self.volume = None
        self.volume_available = False
        self.min_vol = -65.25  # Default dB range
        self.max_vol = 0.0
        self.volume_method = "none"
        
        # Try different volume control methods
        self._initialize_volume_control()
        
        # Gesture parameters - DECREASED SENSITIVITY
        self.min_distance = 20    # Minimum pinch distance (was 30)
        self.max_distance = 280   # Maximum pinch distance (was 200)
        
        # Smoothing for volume changes
        self.volume_history = []
        self.history_length = 8   # Increased from 5 for smoother changes
        self.current_volume = 50  # Track current volume percentage
        
    def _initialize_volume_control(self):
        """Try different methods to initialize volume control."""
        
        # Method 1: Try pycaw with comtypes fix
        if platform.system() == "Windows":
            try:
                print("Attempting Method 1: pycaw with comtypes...")
                
                # Import with error handling
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                
                # Get audio devices
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self.volume = cast(interface, POINTER(IAudioEndpointVolume))
                
                # Get volume range
                vol_range = self.volume.GetVolumeRange()
                self.min_vol = vol_range[0]
                self.max_vol = vol_range[1]
                
                # Get current volume to initialize
                current_vol_db = self.volume.GetMasterVolumeLevel()
                self.current_volume = int(np.interp(current_vol_db, [self.min_vol, self.max_vol], [0, 100]))
                
                self.volume_available = True
                self.volume_method = "pycaw"
                print(f"✓ Volume control initialized via pycaw")
                print(f"  Volume range: {self.min_vol:.2f} dB to {self.max_vol:.2f} dB")
                print(f"  Current volume: {self.current_volume}%")
                return
                
            except Exception as e:
                print(f"  ✗ pycaw failed: {e}")
        
        # Method 2: Try using Windows API directly via ctypes
        if platform.system() == "Windows":
            try:
                print("Attempting Method 2: Direct Windows API...")
                import ctypes
                from ctypes import wintypes
                
                # Load winmm.dll
                self.winmm = ctypes.WinDLL('winmm.dll')
                
                # Get current volume
                test_vol = wintypes.DWORD()
                result = self.winmm.waveOutGetVolume(wintypes.HANDLE(-1), ctypes.byref(test_vol))
                
                if result == 0:
                    # Extract volume percentage
                    left_vol = test_vol.value & 0xFFFF
                    self.current_volume = int((left_vol / 65535) * 100)
                    
                    self.volume_available = True
                    self.volume_method = "winmm"
                    print("✓ Volume control initialized via Windows API")
                    print(f"  Current volume: {self.current_volume}%")
                    return
                    
            except Exception as e:
                print(f"  ✗ Windows API failed: {e}")
        
        # Method 3: Try pulsectl for Linux
        if platform.system() == "Linux":
            try:
                print("Attempting Method 3: pulsectl for Linux...")
                import pulsectl
                
                with pulsectl.Pulse('volume-control') as pulse:
                    for sink in pulse.sink_list():
                        self.current_volume = int(sink.volume.value_flat * 100)
                        break
                
                self.volume_available = True
                self.volume_method = "pulse"
                print("✓ Volume control initialized via PulseAudio")
                print(f"  Current volume: {self.current_volume}%")
                return
                
            except Exception as e:
                print(f"  ✗ PulseAudio failed: {e}")
        
        # Method 4: Try osascript for macOS
        if platform.system() == "Darwin":
            try:
                print("Attempting Method 4: osascript for macOS...")
                import subprocess
                
                # Get current volume
                result = subprocess.run(['osascript', '-e', 'output volume of (get volume settings)'],
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.current_volume = int(result.stdout.strip())
                    self.volume_available = True
                    self.volume_method = "osascript"
                    print("✓ Volume control initialized via osascript")
                    print(f"  Current volume: {self.current_volume}%")
                    return
                    
            except Exception as e:
                print(f"  ✗ osascript failed: {e}")
        
        # All methods failed
        print("⚠ Could not initialize volume control - running in SIMULATION mode")
        print(f"  Platform: {platform.system()}")
        
    def smooth_volume(self, vol_percentage):
        """
        Smooth volume changes to avoid jittery behavior.
        
        Args:
            vol_percentage: Raw volume percentage
            
        Returns:
            Smoothed volume percentage
        """
        self.volume_history.append(vol_percentage)
        
        # Keep history limited
        if len(self.volume_history) > self.history_length:
            self.volume_history.pop(0)
        
        # Return average of recent values
        if len(self.volume_history) > 0:
            return int(np.mean(self.volume_history))
        
        return vol_percentage
    
    def set_volume(self, distance):
        """
        Set system volume based on finger distance.
        
        Args:
            distance: Distance between thumb and index finger
        """
        # Map distance to volume percentage (0-100)
        raw_vol_percentage = np.interp(
            distance, 
            [self.min_distance, self.max_distance], 
            [0, 100]
        )
        raw_vol_percentage = np.clip(raw_vol_percentage, 0, 100)
        
        # Smooth the volume changes
        vol_percentage = self.smooth_volume(raw_vol_percentage)
        
        # Only update if change is significant (reduces micro-adjustments)
        if abs(vol_percentage - self.current_volume) < 2:
            return self.current_volume
        
        self.current_volume = vol_percentage
        
        if not self.volume_available:
            return self.current_volume
        
        try:
            # Method 1: pycaw - Controls MASTER volume
            if self.volume_method == "pycaw":
                vol_db = np.interp(
                    vol_percentage,
                    [0, 100],
                    [self.min_vol, self.max_vol]
                )
                # SetMasterVolumeLevel controls the system master volume
                self.volume.SetMasterVolumeLevel(vol_db, None)
            
            # Method 2: Windows API (winmm) - Controls MASTER volume
            elif self.volume_method == "winmm":
                import ctypes
                from ctypes import wintypes
                
                # Convert percentage to Windows volume format (0-65535 for each channel)
                vol_value = int((vol_percentage / 100) * 65535)
                # Pack left and right channels (both set to same value for balanced output)
                volume_setting = (vol_value << 16) | vol_value
                # waveOutSetVolume controls the master wave output volume
                self.winmm.waveOutSetVolume(wintypes.HANDLE(-1), volume_setting)
            
            # Method 3: PulseAudio (Linux) - Controls default sink volume
            elif self.volume_method == "pulse":
                import pulsectl
                with pulsectl.Pulse('volume-control') as pulse:
                    # Set volume for all sinks (output devices)
                    for sink in pulse.sink_list():
                        pulse.volume_set_all_chans(sink, vol_percentage / 100)
            
            # Method 4: osascript (macOS) - Controls system master volume
            elif self.volume_method == "osascript":
                import subprocess
                # 'set volume output volume' sets the main system volume
                subprocess.run(['osascript', '-e', f'set volume output volume {vol_percentage}'],
                             capture_output=True)
        
        except Exception as e:
            print(f"Error setting volume: {e}")
            self.volume_available = False
        
        return self.current_volume
    
    def get_current_volume(self):
        """Get current system volume."""
        if not self.volume_available:
            return self.current_volume
        
        try:
            if self.volume_method == "pycaw":
                vol_db = self.volume.GetMasterVolumeLevel()
                vol_percentage = np.interp(vol_db, [self.min_vol, self.max_vol], [0, 100])
                return int(vol_percentage)
            
            elif self.volume_method == "winmm":
                import ctypes
                from ctypes import wintypes
                vol = wintypes.DWORD()
                self.winmm.waveOutGetVolume(wintypes.HANDLE(-1), ctypes.byref(vol))
                # Extract left channel volume
                left_vol = vol.value & 0xFFFF
                vol_percentage = (left_vol / 65535) * 100
                return int(vol_percentage)
            
            elif self.volume_method == "pulse":
                import pulsectl
                with pulsectl.Pulse('volume-control') as pulse:
                    for sink in pulse.sink_list():
                        return int(sink.volume.value_flat * 100)
            
            elif self.volume_method == "osascript":
                import subprocess
                result = subprocess.run(['osascript', '-e', 'output volume of (get volume settings)'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    return int(result.stdout.strip())
        
        except Exception as e:
            print(f"Error getting volume: {e}")
        
        return self.current_volume
    
    def draw_volume_bar(self, img, vol_percentage, distance):
        """
        Draw volume bar and visual feedback.
        
        Args:
            img: Input image
            vol_percentage: Current volume percentage (0-100)
            distance: Finger distance
        """
        h, w, _ = img.shape
        
        # Draw volume bar background
        bar_x, bar_y = 50, 150
        bar_w, bar_h = 50, 300
        
        cv2.rectangle(img, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), 
                     (50, 50, 50), 3)
        
        # Draw volume level
        vol_bar_height = int(np.interp(vol_percentage, [0, 100], [bar_h, 0]))
        
        # Color based on volume level
        if vol_percentage < 33:
            vol_color = (0, 255, 0)  # Green
        elif vol_percentage < 66:
            vol_color = (0, 255, 255)  # Yellow
        else:
            vol_color = (0, 100, 255)  # Orange-Red
        
        cv2.rectangle(img, (bar_x, bar_y + vol_bar_height), 
                     (bar_x + bar_w, bar_y + bar_h), vol_color, -1)
        
        # Draw percentage
        cv2.putText(img, f'{vol_percentage}%', (bar_x - 10, bar_y + bar_h + 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Draw distance range indicator
        range_y = bar_y + bar_h + 80
        cv2.putText(img, "Distance Range:", (bar_x - 10, range_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(img, f"{self.min_distance}-{self.max_distance}px", (bar_x - 10, range_y + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Draw instructions box
        overlay = img.copy()
        cv2.rectangle(overlay, (w - 480, 10), (w - 10, 230), (50, 50, 50), -1)
        cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)
        
        # Instructions
        cv2.putText(img, "MASTER Volume Control", (w - 460, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(img, "Pinch to adjust volume", (w - 460, 75),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(img, f"Current Distance: {int(distance)}px", (w - 460, 105),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Show smoothing status
        smoothness = len(self.volume_history)
        cv2.putText(img, f"Smoothing: {smoothness}/{self.history_length}", (w - 460, 135),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Show mode status
        if self.volume_available:
            mode_text = f"ACTIVE ({self.volume_method})"
            mode_color = (0, 255, 0)
            status_text = "Controlling MASTER Volume"
        else:
            mode_text = "SIMULATION MODE"
            mode_color = (0, 165, 255)
            status_text = "Visual Only - No Control"
        
        cv2.putText(img, f"Mode: {mode_text}", (w - 460, 165),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, mode_color, 2)
        cv2.putText(img, status_text, (w - 460, 190),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, mode_color, 1)
        
        cv2.putText(img, f"Platform: {platform.system()}", (w - 460, 210),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Instructions to quit
        cv2.rectangle(img, (w - 250, h - 50), (w - 10, h - 10), (50, 50, 50), -1)
        cv2.putText(img, "Press 'q' to quit", (w - 240, h - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return img

def main():
    """
    Main volume control application.
    """
    # Initialize
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)
    cap.set(4, 720)
    
    print("\n" + "="*70)
    print("       MASTER VOLUME CONTROL WITH HAND GESTURES")
    print("="*70)
    print("\nInstructions:")
    print("  • Show your hand to the camera")
    print("  • Pinch thumb and index finger together = Lower volume")
    print("  • Move fingers apart = Increase volume")
    print("  • Slower movements = More precise control")
    print("  • Press 'q' to quit\n")
    print("Sensitivity Settings:")
    print(f"  • Distance range: 20-280 pixels (wider range = less sensitive)")
    print(f"  • Smoothing: 8 frame average (smoother changes)")
    print(f"  • Minimum change: 2% (reduces jitter)")
    print("="*70 + "\n")
    
    controller = VolumeController()
    
    if not controller.volume_available:
        print("\n💡 TROUBLESHOOTING:")
        if platform.system() == "Windows":
            print("   For Windows, try:")
            print("   1. pip uninstall comtypes pycaw -y")
            print("   2. pip install comtypes==1.1.14")
            print("   3. pip install pycaw")
            print("   4. python -c \"import comtypes; import shutil; shutil.rmtree(comtypes.client._code_cache.__path__[0], ignore_errors=True)\"")
        elif platform.system() == "Linux":
            print("   For Linux: pip install pulsectl")
        elif platform.system() == "Darwin":
            print("   macOS should work with osascript (built-in)")
        print()
    else:
        print(f"✓ Ready to control MASTER system volume!")
        print(f"  Initial volume: {controller.current_volume}%\n")
    
    print("Starting camera...\n")
    
    while True:
        success, img = cap.read()
        if not success:
            print("Failed to grab frame")
            break
        
        img = cv2.flip(img, 1)
        
        # Detect hand
        img = controller.detector.find_hands(img)
        landmark_list = controller.detector.find_position(img, draw=False)
        
        vol_percentage = controller.current_volume
        distance = 0
        
        if len(landmark_list) != 0:
            # Get thumb tip (4) and index tip (8) positions
            x1, y1 = landmark_list[4][1], landmark_list[4][2]
            x2, y2 = landmark_list[8][1], landmark_list[8][2]
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            
            # Draw connection with thickness based on distance
            thickness = 3 if distance > 50 else 5
            cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), thickness)
            
            # Calculate distance
            distance = math.hypot(x2 - x1, y2 - y1)
            
            # Visual feedback on center point - changes with distance
            if distance < 50:
                cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)
                cv2.putText(img, "MIN", (cx - 20, cy - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            elif distance > 250:
                cv2.circle(img, (cx, cy), 15, (0, 100, 255), cv2.FILLED)
                cv2.putText(img, "MAX", (cx - 20, cy - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 100, 255), 2)
            else:
                cv2.circle(img, (cx, cy), 12, (255, 0, 255), cv2.FILLED)
            
            # Set volume
            vol_percentage = controller.set_volume(distance)
        
        # Draw UI
        img = controller.draw_volume_bar(img, vol_percentage, distance)
        
        # Display
        cv2.imshow("Master Volume Control - Hand Gestures", img)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("\n✓ Volume control closed")
    print(f"✓ Final volume: {controller.current_volume}%")

if __name__ == "__main__":
    main()