"""
Serial controller for Arduino-based prosthetic hand.

Protocol: 3-byte packet sent every frame:
  [0xAA, gripper_angle (0-180), wrist_angle (0-180)]

  gripper_angle: derived from hand openness (fingertip spread)
  wrist_angle:   derived from hand tilt angle
"""
import math
import threading

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

START_BYTE = 0xAA

# MediaPipe landmark indices
WRIST      = 0
INDEX_MCP  = 5
FINGERTIPS = [4, 8, 12, 16, 20]
FINGER_MCPS = [2, 5, 9, 13, 17]


def list_ports():
    if not SERIAL_AVAILABLE:
        return []
    return [p.device for p in serial.tools.list_ports.comports()]


def find_arduino():
    """Auto-detect Arduino by USB vendor ID or port name."""
    if not SERIAL_AVAILABLE:
        return None
    for p in serial.tools.list_ports.comports():
        # Arduino vendor IDs or usbmodem/usbserial in port name
        if p.vid in (0x2341, 0x1A86, 0x0403, 0x10C4) or \
           any(x in p.device for x in ("usbmodem", "usbserial", "ttyUSB", "ttyACM")):
            return p.device
    return None


def _dist(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


# (tip, pip) pairs for index, middle, ring, pinky
_FINGER_JOINTS = [(8, 6), (12, 10), (16, 14), (20, 18)]

def calc_gripper_angle(landmark_list):
    """
    Returns 0–88 based on how many fingers are curled.
    A finger is curled when its tip is below its PIP joint (Y increases downward).
    0 = fully open, 88 = fully closed fist.
    """
    if not landmark_list or len(landmark_list) < 21:
        return 0
    curled = sum(
        1 for tip, pip in _FINGER_JOINTS
        if landmark_list[tip][1] > landmark_list[pip][1]
    )
    return curled * 22  # 0, 22, 44, 66, 88


def calc_wrist_angle(landmark_list):
    """Returns 0-45 representing wrist tilt."""
    if not landmark_list or len(landmark_list) < 21:
        return 0
    dx = landmark_list[INDEX_MCP][0] - landmark_list[WRIST][0]
    dy = landmark_list[INDEX_MCP][1] - landmark_list[WRIST][1]
    angle_rad = math.atan2(-dy, dx)
    angle_deg = math.degrees(angle_rad)
    return int((angle_deg + 90) % 180 / 180 * 45)


class ArduinoController:
    """
    Streams gripper and wrist servo angles to Arduino every frame.

    Usage:
        ctrl = ArduinoController(port="/dev/cu.usbmodem1101", baud=115200)
        ctrl.connect()
        ctrl.send_frame(landmark_list)   # call each video frame
        ctrl.disconnect()
    """

    def __init__(self, port, baud=9600, dry_run=False):
        self.port = port
        self.baud = baud
        self.dry_run = dry_run
        self._serial = None
        self._lock = threading.Lock()
        self._state = 0          # current servo state (0 or 90)
        self._smoothed = 0.0     # EMA — starts at open so first frame can't trigger closed

    def connect(self):
        if self.dry_run:
            print(f"[Arduino] DRY RUN — would connect to {self.port} @ {self.baud} baud")
            return
        if not SERIAL_AVAILABLE:
            raise RuntimeError("pyserial not installed. Run: pip install pyserial")
        import time
        self._serial = serial.Serial(self.port, self.baud, timeout=5)
        print(f"[Arduino] Waiting for ready signal on {self.port}...")
        deadline = time.time() + 10
        while time.time() < deadline:
            if self._serial.in_waiting:
                byte = self._serial.read(1)
                if byte == b'\xBB':
                    break
        else:
            print("[Arduino] Warning: no ready signal received, proceeding anyway")
        self._serial.timeout = 1
        print(f"[Arduino] Connected to {self.port} @ {self.baud} baud")

    def disconnect(self):
        if self._serial and self._serial.is_open:
            self._serial.close()
            print("[Arduino] Disconnected")

    def is_connected(self):
        return self.dry_run or (self._serial is not None and self._serial.is_open)

    def send_frame(self, landmark_list):
        """Snap to 0 or 90 using EMA smoothing + hysteresis to avoid flickering."""
        raw = calc_gripper_angle(landmark_list)

        self._smoothed += 0.25 * (raw - self._smoothed)

        # Calibrated thresholds — open hand: 0-10, closed fist: 60-90
        # Dead zone 20-40 prevents any flickering at the boundary
        if self._state == 0 and self._smoothed > 55:
            self._state = 90
            self._send(90)
            print("[Servo] → 90° (closed)")
        elif self._state == 90 and self._smoothed < 25:
            self._state = 0
            self._send(0)
            print("[Servo] → 0° (open)")

        return self._state, int(self._smoothed)

    def send_idle(self):
        """Send open position when no hand is detected."""
        self._send(0)

    def _send(self, finger):
        if self.dry_run:
            print(f"[Arduino] finger={finger}°")
            return
        with self._lock:
            if self._serial and self._serial.is_open:
                self._serial.write(bytes([finger]))

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()
