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
WRIST       = 0
INDEX_MCP   = 5
FINGERTIPS  = [4, 8, 12, 16, 20]
FINGER_MCPS = [2, 5, 9, 13, 17]


def list_ports():
    if not SERIAL_AVAILABLE:
        return []
    return [p.device for p in serial.tools.list_ports.comports()]


def _dist(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def calc_gripper_angle(landmark_list):
    """
    Returns 0-180 representing how open the hand is.
    Measures average fingertip distance from their MCP base joints,
    normalized against the palm size (wrist to middle MCP).
    """
    if not landmark_list or len(landmark_list) < 21:
        return 90

    palm_size = _dist(landmark_list[WRIST], landmark_list[9])
    if palm_size < 1:
        return 90

    spread = sum(
        _dist(landmark_list[tip], landmark_list[mcp])
        for tip, mcp in zip(FINGERTIPS, FINGER_MCPS)
    ) / len(FINGERTIPS)

    # Normalize: ~0.5x palm = closed, ~1.8x palm = fully open
    ratio = (spread / palm_size - 0.5) / 1.3
    angle = int(max(0, min(1, ratio)) * 45)
    return angle


def calc_wrist_angle(landmark_list):
    """
    Returns 0-180 representing wrist tilt.
    Uses the angle of the line from wrist to index MCP (knuckle).
    Upright hand = 90, tilted left = 0, tilted right = 180.
    """
    if not landmark_list or len(landmark_list) < 21:
        return 90

    dx = landmark_list[INDEX_MCP][0] - landmark_list[WRIST][0]
    dy = landmark_list[INDEX_MCP][1] - landmark_list[WRIST][1]
    angle_rad = math.atan2(-dy, dx)          # flip y (image coords)
    angle_deg = math.degrees(angle_rad)      # -180 to 180
    servo = int((angle_deg + 90) % 180 / 180 * 45)  # map to 0-45
    return servo


class ArduinoController:
    """
    Streams gripper and wrist servo angles to Arduino every frame.

    Usage:
        ctrl = ArduinoController(port="/dev/cu.usbmodem1101", baud=115200)
        ctrl.connect()
        ctrl.send_frame(landmark_list)   # call each video frame
        ctrl.disconnect()
    """

    def __init__(self, port, baud=115200, dry_run=False):
        self.port = port
        self.baud = baud
        self.dry_run = dry_run
        self._serial = None
        self._lock = threading.Lock()

    def connect(self):
        if self.dry_run:
            print(f"[Arduino] DRY RUN — would connect to {self.port} @ {self.baud} baud")
            return
        if not SERIAL_AVAILABLE:
            raise RuntimeError("pyserial not installed. Run: pip install pyserial")
        import time
        self._serial = serial.Serial(self.port, self.baud, timeout=1)
        time.sleep(2)
        print(f"[Arduino] Connected to {self.port} @ {self.baud} baud")

    def disconnect(self):
        if self._serial and self._serial.is_open:
            self._serial.close()
            print("[Arduino] Disconnected")

    def is_connected(self):
        return self.dry_run or (self._serial is not None and self._serial.is_open)

    def send_frame(self, landmark_list):
        """Calculate angles from landmarks and send to Arduino."""
        gripper = calc_gripper_angle(landmark_list)
        wrist   = calc_wrist_angle(landmark_list)
        self._send(gripper, wrist)
        return gripper, wrist

    def send_idle(self):
        """Send neutral position when no hand is detected."""
        self._send(22, 22)

    def _send(self, gripper_angle, wrist_angle):
        packet = bytes([START_BYTE, gripper_angle, wrist_angle])
        if self.dry_run:
            print(f"[Arduino] gripper={gripper_angle}° wrist={wrist_angle}°")
            return
        with self._lock:
            if self._serial and self._serial.is_open:
                self._serial.write(packet)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()
