"""
Serial controller for Arduino-based prosthetic hand.

Protocol (single byte per command):
  0x01  OPEN_GRIPPER
  0x02  CLOSE_GRIPPER
  0x03  PINCH
  0x04  ROTATE_CW
  0x05  ROTATE_CCW
  0x06  HOLD
  0xFF  PING (Arduino echoes 0xFF back as a health check)

Arduino sketch must read Serial.read() and act on these bytes.
"""
import time
import threading
from collections import deque, Counter

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


GESTURE_COMMANDS = {
    0: 0x01,  # open hand  → open gripper
    1: 0x02,  # close hand → close gripper
    2: 0x03,  # pointer    → pinch
}

MOTION_COMMANDS = {
    0: 0x06,  # stationary     → hold
    1: 0x04,  # clockwise      → rotate CW
    2: 0x05,  # counterclockwise → rotate CCW
    3: 0x06,  # moving         → hold
}

COMMAND_NAMES = {
    0x01: "OPEN_GRIPPER",
    0x02: "CLOSE_GRIPPER",
    0x03: "PINCH",
    0x04: "ROTATE_CW",
    0x05: "ROTATE_CCW",
    0x06: "HOLD",
    0xFF: "PING",
}


def list_ports():
    """Return available serial ports — helps identify which one is the Arduino."""
    if not SERIAL_AVAILABLE:
        return []
    return [p.device for p in serial.tools.list_ports.comports()]


class GestureDebouncer:
    """Emits a gesture ID only when it has been stable for `threshold` frames."""

    def __init__(self, threshold=8):
        self.threshold = threshold
        self._history = deque(maxlen=threshold)
        self._last_sent = None

    def update(self, gesture_id):
        self._history.append(gesture_id)
        if len(self._history) < self.threshold:
            return None
        most_common, count = Counter(self._history).most_common(1)[0]
        if count >= self.threshold and most_common != self._last_sent:
            self._last_sent = most_common
            return most_common
        return None

    def reset(self):
        self._history.clear()
        self._last_sent = None


class ArduinoController:
    """
    Manages serial connection to an Arduino and sends prosthetic commands.

    Usage:
        ctrl = ArduinoController(port="/dev/cu.usbmodem14101", baud=9600)
        ctrl.connect()
        ctrl.send_gesture(gesture_id=1)   # close gripper
        ctrl.send_motion(motion_id=1)     # rotate CW
        ctrl.disconnect()

    With context manager:
        with ArduinoController(port=...) as ctrl:
            ctrl.send_gesture(0)
    """

    def __init__(self, port, baud=9600, timeout=1.0, debounce_threshold=8, dry_run=False):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.dry_run = dry_run  # if True, prints commands instead of sending
        self._serial = None
        self._lock = threading.Lock()
        self._gesture_debouncer = GestureDebouncer(threshold=debounce_threshold)
        self._motion_debouncer = GestureDebouncer(threshold=debounce_threshold)

    def connect(self):
        if self.dry_run:
            print(f"[Arduino] DRY RUN — would connect to {self.port} @ {self.baud} baud")
            return
        if not SERIAL_AVAILABLE:
            raise RuntimeError("pyserial not installed. Run: pip install pyserial")
        self._serial = serial.Serial(self.port, self.baud, timeout=self.timeout)
        time.sleep(2)  # Arduino resets on serial connect, wait for it to boot
        print(f"[Arduino] Connected to {self.port} @ {self.baud} baud")

    def disconnect(self):
        if self._serial and self._serial.is_open:
            self._serial.close()
            print("[Arduino] Disconnected")

    def is_connected(self):
        if self.dry_run:
            return True
        return self._serial is not None and self._serial.is_open

    def send_raw(self, byte_value):
        name = COMMAND_NAMES.get(byte_value, f"0x{byte_value:02X}")
        if self.dry_run:
            print(f"[Arduino] SEND → {name}")
            return
        with self._lock:
            if self._serial and self._serial.is_open:
                self._serial.write(bytes([byte_value]))

    def send_gesture(self, gesture_id):
        """Send command for a hand sign gesture (debounced)."""
        stable_id = self._gesture_debouncer.update(gesture_id)
        if stable_id is not None and stable_id in GESTURE_COMMANDS:
            self.send_raw(GESTURE_COMMANDS[stable_id])

    def send_motion(self, motion_id):
        """Send command for a motion gesture (debounced)."""
        stable_id = self._motion_debouncer.update(motion_id)
        if stable_id is not None and stable_id in MOTION_COMMANDS:
            self.send_raw(MOTION_COMMANDS[stable_id])

    def ping(self):
        """Check if Arduino is responsive. Returns True if it echoes back."""
        if self.dry_run:
            return True
        self.send_raw(0xFF)
        time.sleep(0.1)
        if self._serial and self._serial.in_waiting:
            response = self._serial.read(1)
            return response == b'\xFF'
        return False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()
