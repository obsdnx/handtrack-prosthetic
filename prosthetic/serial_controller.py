"""
================================================================
  serial_controller.py  —  SIMPLE OPEN/CLOSE
================================================================
  Arduino firmware: prosthetic_hand.ino

  Counts how many fingers are curled. When enough fingers are
  curled (smoothed score > 55) all 5 servos close together.
  When hand opens (score < 25) all 5 servos open together.
  EMA smoothing + hysteresis prevents flickering.
================================================================
"""
import threading

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

# (tip, pip) landmark pairs — tip Y > pip Y means finger is curled
_FINGER_JOINTS = [(8, 6), (12, 10), (16, 14), (20, 18)]


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


def calc_gripper_angle(landmark_list):
    """
    Returns 0–88 based on how many fingers are curled.
    0 = fully open, 88 = fully closed fist.
    """
    if not landmark_list or len(landmark_list) < 21:
        return 0
    curled = sum(
        1 for tip, pip in _FINGER_JOINTS
        if landmark_list[tip][1] > landmark_list[pip][1]
    )
    return curled * 22  # 0, 22, 44, 66, 88


class ArduinoController:
    """
    Sends open/close commands to all 5 servos simultaneously.
    Snaps between 0° (open) and 180° (closed) using EMA + hysteresis.
    """

    def __init__(self, port, baud=9600, dry_run=False):
        self.port = port
        self.baud = baud
        self.dry_run = dry_run
        self._serial = None
        self._lock = threading.Lock()
        self._state = 0        # 0=open, 180=closed
        self._smoothed = 0.0

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
        raw = calc_gripper_angle(landmark_list)
        self._smoothed += 0.25 * (raw - self._smoothed)

        if self._state == 0 and self._smoothed > 55:
            self._state = 180
            self._send(finger_angle=0, thumb_angle=180)
            print("[Servo] → closed")
        elif self._state == 180 and self._smoothed < 25:
            self._state = 0
            self._send(finger_angle=180, thumb_angle=0)
            print("[Servo] → open")

        return self._state, int(self._smoothed)

    def send_idle(self):
        if self._state != 0:
            self._state = 0
            self._send(finger_angle=180, thumb_angle=0)

    def _send(self, finger_angle, thumb_angle):
        """Send 6-byte packet: fingers get finger_angle, thumb gets thumb_angle."""
        if self.dry_run:
            print(f"[Arduino] fingers → {finger_angle}°  thumb → {thumb_angle}°")
            return
        with self._lock:
            if self._serial and self._serial.is_open:
                self._serial.write(bytes([
                    0xAA,
                    thumb_angle,                                      # pin 9
                    finger_angle, finger_angle, finger_angle,         # pins 10-12
                    finger_angle,                                     # pin 13
                ]))

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()
