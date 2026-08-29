"""
================================================================
  test_servo_min.py  —  MINIMAL SANITY CHECK
================================================================
  Arduino firmware: prosthetic_hand.ino  (simple open/close)

  The simplest possible serial test. Sends a single raw byte
  (no start byte, no framing) and checks that the servos respond.
  Use this first if you suspect a serial communication problem.

  Sends: 90° (closed) → 0° (open), three rounds with 2s holds.

  Usage:
    python test_servo_min.py
    python test_servo_min.py /dev/cu.usbmodemXXXX
================================================================
"""
import sys, time, serial, serial.tools.list_ports

def find_arduino():
    for p in serial.tools.list_ports.comports():
        if p.vid in (0x2341, 0x1A86, 0x0403, 0x10C4) or \
           any(x in p.device for x in ("usbmodem", "usbserial", "ttyUSB", "ttyACM")):
            return p.device
    return None

PORT = sys.argv[1] if len(sys.argv) > 1 else find_arduino()
if not PORT:
    print("No Arduino found.")
    sys.exit(1)

print(f"Connecting to {PORT} @ 9600...")
ser = serial.Serial(PORT, 9600, timeout=2)

print("Waiting 3.5s for startup sweep...")
time.sleep(3.5)

for i in range(1, 4):
    print(f"\n--- Round {i}/3 ---")
    print("→ 90° (closed)")
    ser.write(bytes([90]))
    time.sleep(2)
    print("→ 0° (open)")
    ser.write(bytes([0]))
    time.sleep(2)

print("\nDone.")
ser.close()
