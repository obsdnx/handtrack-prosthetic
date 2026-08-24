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


def calc_gripper_angle(landmark_list):
    """Returns 0-45 representing how open the hand is."""
    if not landmark_list or len(landmark_list) < 21:
        return 0
    palm_size = _dist(landmark_list[WRIST], landmark_list[9])
    if palm_size < 1:
        return 0
    spread = sum(
        _dist(landmark_list[tip], landmark_list[mcp])
        for tip, mcp in zip(FINGERTIPS, FINGER_MCPS)
    ) / len(FINGERTIPS)
    ratio = (spread / palm_size - 0.5) / 1.3
    return int((1 - max(0, min(1, ratio))) * 90)  # 0=closed, 90=open


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
        """Calculate finger angle from landmarks and send."""
        finger = calc_gripper_angle(landmark_list)
        self._send(finger)
        return finger

    def send_idle(self):
        """Send open position when no hand is detected."""
        self._send(0)

    def _send(self, finger):
        packet = bytes([START_BYTE, finger])
        if self.dry_run:
            print(f"[Arduino] finger={finger}°")
            return
        with self._lock:
            if self._serial and self._serial.is_open:
                self._serial.write(packet)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()
