"""
Serial controller for Arduino-based prosthetic hand.

Protocol: 6-byte packet [0xAA, pinky, ring, middle, index, thumb]
  Each finger gets its own angle (0=closed, 180=open).
  Thumb is pre-inverted in Python to cancel Arduino-side inversion.
"""
import threading

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

START_BYTE = 0xAA

# (tip, pip) landmark pairs — Y increases downward, tip > pip means curled
_JOINTS = [
    (20, 18),  # pinky
    (16, 14),  # ring
    (12, 10),  # middle
    ( 8,  6),  # index
]


def list_ports():
    if not SERIAL_AVAILABLE:
        return []
    return [p.device for p in serial.tools.list_ports.comports()]


def find_arduino():
    if not SERIAL_AVAILABLE:
        return None
    for p in serial.tools.list_ports.comports():
        if p.vid in (0x2341, 0x1A86, 0x0403, 0x10C4) or \
           any(x in p.device for x in ("usbmodem", "usbserial", "ttyUSB", "ttyACM")):
            return p.device
    return None


def calc_finger_angles(landmark_list):
    """
    Returns [pinky, ring, middle, index, thumb] angles (0=closed, 180=open).
    Fingers: tip Y > pip Y means curled → 0.
    Thumb: tip Y > wrist Y by a margin means curled toward palm → 0.
    """
    if not landmark_list or len(landmark_list) < 21:
        return [180] * 5

    angles = []
    for tip, pip in _JOINTS:
        angles.append(0 if landmark_list[tip][1] > landmark_list[pip][1] else 180)

    # Thumb — use distance from tip (4) to index MCP (5), normalized by hand size
    # When thumb curls inward it moves toward the index base regardless of hand orientation
    def dist(a, b):
        return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** 0.5
    thumb_dist = dist(landmark_list[4], landmark_list[5])
    hand_scale = dist(landmark_list[0], landmark_list[9])  # wrist to middle MCP
    thumb_curled = hand_scale > 0 and (thumb_dist / hand_scale) < 0.3
    angles.append(0 if thumb_curled else 180)

    return angles  # [pinky, ring, middle, index, thumb]


class ArduinoController:
    """
    Streams per-finger angles to Arduino every frame.

    Uses a vote counter per finger: must see the same state VOTE_THRESHOLD
    frames in a row before committing, preventing twitching without adding lag.
    Thumb angle is pre-inverted to cancel Arduino-side inversion.
    """

    VOTE_THRESHOLD = 3  # ~90ms at 30fps before a state change commits

    def __init__(self, port, baud=9600, dry_run=False):
        self.port = port
        self.baud = baud
        self.dry_run = dry_run
        self._serial = None
        self._lock = threading.Lock()
        self._states     = [180] * 5  # committed state per finger
        self._candidates = [180] * 5  # what we're voting toward
        self._votes      = [0]   * 5  # consecutive frames at candidate

    def connect(self):
        if self.dry_run:
            print(f"[Arduino] DRY RUN — would connect to {self.port} @ {self.baud} baud")
            return
        if not SERIAL_AVAILABLE:
            raise RuntimeError("pyserial not installed. Run: pip install pyserial")
        import time
        self._serial = serial.Serial(self.port, self.baud, timeout=5)
        time.sleep(2)
        self._serial.reset_input_buffer()
        self._serial.timeout = 1
        print(f"[Arduino] Connected to {self.port} @ {self.baud} baud")

    def disconnect(self):
        if self._serial and self._serial.is_open:
            self._serial.close()
            print("[Arduino] Disconnected")

    def is_connected(self):
        return self.dry_run or (self._serial is not None and self._serial.is_open)

    def send_frame(self, landmark_list, gesture_label=None):
        raw = calc_finger_angles(landmark_list)
        changed = False

        for i, angle in enumerate(raw):
            if angle == self._states[i]:
                self._votes[i] = 0
                self._candidates[i] = angle
            else:
                if angle != self._candidates[i]:
                    self._candidates[i] = angle
                    self._votes[i] = 1
                else:
                    self._votes[i] += 1

                if self._votes[i] >= self.VOTE_THRESHOLD:
                    self._states[i] = angle
                    self._votes[i] = 0
                    changed = True

        if changed:
            self._send_packet(self._states)

        return list(self._states)

    def send_idle(self):
        target = [180] * 5
        if self._states != target:
            self._states = target
            self._candidates = list(target)
            self._votes = [0] * 5
            self._send_packet(self._states)

    def _send_packet(self, states):
        pinky, ring, middle, index, thumb = states
        thumb_out = 180 - thumb  # pre-inverted to cancel Arduino-side inversion
        s = lambda a: "O" if a == 180 else "C"
        print(f"[Servo] PK:{s(pinky)} RG:{s(ring)} MD:{s(middle)} IX:{s(index)} TH:{s(thumb)}")
        if self.dry_run:
            return
        with self._lock:
            if self._serial and self._serial.is_open:
                self._serial.write(bytes([START_BYTE, pinky, ring, middle, index, thumb_out]))

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()
