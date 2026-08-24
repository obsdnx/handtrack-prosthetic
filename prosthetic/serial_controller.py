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

# MediaPipe landmark indices per finger: (tip, pip, mcp)
WRIST = 0
FINGERS = {
    "thumb":  (4,  3,  2),
    "index":  (8,  7,  5),
    "middle": (12, 11, 9),
    "ring":   (16, 15, 13),
}


def list_ports():
    if not SERIAL_AVAILABLE:
        return []
    return [p.device for p in serial.tools.list_ports.comports()]


def _dist(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def calc_finger_angle(landmark_list, tip_idx, pip_idx, mcp_idx):
    """
    Returns 0-45 for a single finger.
    0 = fully curled, 45 = fully extended.
    Measured as tip-to-mcp distance normalized by palm size.
    """
    if not landmark_list or len(landmark_list) < 21:
        return 0

    palm_size = _dist(landmark_list[WRIST], landmark_list[9])
    if palm_size < 1:
        return 0

    extension = _dist(landmark_list[tip_idx], landmark_list[mcp_idx])
    ratio = (extension / palm_size - 0.4) / 1.2
    return int(max(0, min(1, ratio)) * 45)


def calc_all_finger_angles(landmark_list):
    """Returns [thumb, index, middle, ring] angles, each 0-45."""
    return [
        calc_finger_angle(landmark_list, *indices)
        for indices in FINGERS.values()
    ]


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
        """Calculate per-finger angles from landmarks and send to Arduino."""
        angles = calc_all_finger_angles(landmark_list)
        self._send(angles)
        return angles

    def send_idle(self):
        """Send closed position when no hand is detected."""
        self._send([0, 0, 0, 0])

    def _send(self, angles):
        packet = bytes([START_BYTE, *angles])
        if self.dry_run:
            names = ["thumb", "index", "middle", "ring"]
            parts = "  ".join(f"{n}={a}°" for n, a in zip(names, angles))
            print(f"[Arduino] {parts}")
            return
        with self._lock:
            if self._serial and self._serial.is_open:
                self._serial.write(packet)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()
