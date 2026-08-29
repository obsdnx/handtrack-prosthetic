"""
================================================================
  test_live_fingers.py  —  LIVE FINGER DETECTION + ARDUINO
================================================================
  Arduino firmware: finger_control.ino  (per-finger)

  Same as running app.py --arduino but stripped down:
  no gesture classifier, no overlays, no recording.
  Just the camera, finger detection, and clear terminal logs
  showing exactly what is being sent to each servo.

  Use this to verify the Arduino is receiving correct angles
  before running the full app.

  Usage:
    python test_live_fingers.py
    python test_live_fingers.py /dev/cu.usbmodemXXXX

  Terminal output:
    [Servo] PK:O RG:C MD:O IX:O TH:O   (O=open C=closed)

  Press ESC or Q in the camera window to quit.
================================================================
"""
import sys
import time
import threading
import cv2 as cv
import mediapipe as mp

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    print("ERROR: pyserial not installed. Run: pip install pyserial")
    sys.exit(1)

START_BYTE = 0xAA
VOTE_THRESHOLD = 3   # frames of agreement before committing a state change
SEND_INTERVAL  = 0.1  # max 10 sends/second

# (tip, pip) landmark pairs for pinky, ring, middle, index
_JOINTS = [(20, 18), (16, 14), (12, 10), (8, 6)]


def find_arduino():
    for p in serial.tools.list_ports.comports():
        if p.vid in (0x2341, 0x1A86, 0x0403, 0x10C4) or \
           any(x in p.device for x in ("usbmodem", "usbserial", "ttyUSB", "ttyACM")):
            return p.device
    return None


def calc_finger_angles(lm):
    """Returns [pinky, ring, middle, index, thumb] — 0=closed, 180=open."""
    if not lm or len(lm) < 21:
        return [180] * 5
    angles = [0 if lm[tip][1] > lm[pip][1] else 180 for tip, pip in _JOINTS]
    def dist(a, b): return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** 0.5
    thumb_dist = dist(lm[4], lm[5])
    hand_scale = dist(lm[0], lm[9])
    thumb_curled = hand_scale > 0 and (thumb_dist / hand_scale) < 0.4
    angles.append(0 if thumb_curled else 180)
    return angles


def calc_landmark_list(image, landmarks):
    h, w = image.shape[:2]
    return [[min(int(lm.x * w), w-1), min(int(lm.y * h), h-1)]
            for lm in landmarks.landmark]


class FingerSender:
    def __init__(self, port, baud=9600):
        self.port = port
        self.baud = baud
        self._serial = None
        self._lock = threading.Lock()
        self._states     = [180] * 5
        self._candidates = [180] * 5
        self._votes      = [0]   * 5

    def connect(self):
        print(f"Connecting to {self.port} @ {self.baud}...")
        self._serial = serial.Serial(self.port, self.baud, timeout=5)
        time.sleep(2)
        self._serial.reset_input_buffer()
        self._serial.timeout = 1
        print(f"Connected. Starting detection...\n")

    def disconnect(self):
        if self._serial and self._serial.is_open:
            self._serial.close()
            print("\n[Arduino] Disconnected")

    def update(self, landmark_list):
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
                if self._votes[i] >= VOTE_THRESHOLD:
                    self._states[i] = angle
                    self._votes[i] = 0
                    changed = True
        if changed:
            self._send(self._states)

    def open_all(self):
        if self._states != [180] * 5:
            self._states = [180] * 5
            self._candidates = [180] * 5
            self._votes = [0] * 5
            self._send(self._states)

    def _send(self, states):
        pk, rg, md, ix, th = states
        s = lambda a: "O" if a == 180 else "C"
        print(f"[Servo] TH:{s(th)} IX:{s(ix)} MD:{s(md)} RG:{s(rg)} PK:{s(pk)}")
        with self._lock:
            if self._serial and self._serial.is_open:
                # Packet order matches PINS = {12, 11, 10, 9, 13}
                # Firmware inverts thumb (index 0) as 160 - angle
                self._serial.write(bytes([START_BYTE, th, ix, md, rg, pk]))


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else find_arduino()
    if not port:
        print("No Arduino found. Plug it in or pass the port as an argument.")
        sys.exit(1)

    sender = FingerSender(port)
    sender.connect()

    hands = mp.solutions.hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5,
    )

    cap = cv.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not open camera.")
        sender.disconnect()
        sys.exit(1)

    cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)

    last_send = 0.0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv.flip(frame, 1)
            rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            results = hands.process(rgb)

            now = time.monotonic()
            if now - last_send >= SEND_INTERVAL:
                if results.multi_hand_landmarks:
                    lm = calc_landmark_list(frame, results.multi_hand_landmarks[0])
                    sender.update(lm)
                else:
                    sender.open_all()
                last_send = now

            # Draw detected hand skeleton
            if results.multi_hand_landmarks:
                mp.solutions.drawing_utils.draw_landmarks(
                    frame,
                    results.multi_hand_landmarks[0],
                    mp.solutions.hands.HAND_CONNECTIONS,
                )

            cv.imshow("Live Finger Detection  (ESC/Q to quit)", frame)
            key = cv.waitKey(10) & 0xFF
            if key in (27, ord("q")):
                break

    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv.destroyAllWindows()
        sender.disconnect()


if __name__ == "__main__":
    main()
