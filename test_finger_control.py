"""
================================================================
  test_finger_control.py  —  INTERACTIVE PER-FINGER CONTROL
================================================================
  Arduino firmware: finger_control.ino  (per-finger)

  Type a finger number and angle to move one finger at a time,
  or "all <angle>" to move all fingers together. The current
  state of all other fingers is preserved between commands.

  Usage:
    python test_finger_control.py
    python test_finger_control.py /dev/cu.usbmodemXXXX

  Input format:  <finger 1-5> <angle 0-180>
    Fingers:  1=pinky  2=ring  3=middle  4=index  5=thumb
    Angles:   0=closed  180=open  (anything between is valid)

  Examples:
    1 0       → close pinky only
    3 90      → middle finger to midpoint
    5 0       → close thumb
    all 0     → close all fingers (fist)
    all 180   → open all fingers
================================================================
"""
import sys
import time
import serial
import serial.tools.list_ports

FINGER_NAMES = {1: "pinky", 2: "ring", 3: "middle", 4: "index", 5: "thumb"}


def find_arduino():
    for p in serial.tools.list_ports.comports():
        if p.vid in (0x2341, 0x1A86, 0x0403, 0x10C4) or \
           any(x in p.device for x in ("usbmodem", "usbserial", "ttyUSB", "ttyACM")):
            return p.device
    return None


PORT = sys.argv[1] if len(sys.argv) > 1 else find_arduino()
if not PORT:
    print("No Arduino found. Plug it in or pass the port as an argument.")
    sys.exit(1)

print(f"Connecting to {PORT} @ 9600...")
ser = serial.Serial(PORT, 9600, timeout=2)
time.sleep(2)
ser.reset_input_buffer()
print("Ready. Examples: '1 0'  '3 90'  'all 180'  Ctrl+C to quit.\n")


current = [180, 180, 180, 180, 180]  # pinky, ring, middle, index, thumb


def send_all(angles):
    packet = bytes([0xAA, *angles])
    ser.write(packet)
    echo = ser.read(1)
    labels = [f"{FINGER_NAMES[i+1]}:{'O' if a==180 else 'C'}" for i, a in enumerate(angles)]
    if echo == b'\xAA':
        print(f"  ✓ {' '.join(labels)}")
    else:
        print(f"  ✗ no echo — {' '.join(labels)}")


try:
    while True:
        raw = input("finger angle: ").strip().lower()
        if not raw:
            continue

        parts = raw.split()
        if len(parts) != 2:
            print("  Format: <finger 1-5> <angle 0-180>  or  all <angle>")
            continue

        finger_str, angle_str = parts

        try:
            angle = int(angle_str)
        except ValueError:
            print("  Angle must be a number 0–180")
            continue
        if not 0 <= angle <= 180:
            print("  Angle out of range (0–180)")
            continue

        if finger_str == "all":
            current[:] = [angle] * 5
        else:
            try:
                finger = int(finger_str)
            except ValueError:
                print("  Finger must be 1–5 or 'all'")
                continue
            if not 1 <= finger <= 5:
                print("  Finger out of range (1–5)")
                continue
            current[finger - 1] = angle

        send_all(current)

except KeyboardInterrupt:
    print("\nDone.")
finally:
    ser.close()
