"""
================================================================
  test_servo_direct.py  —  AUTOMATED OPEN/CLOSE SWEEP
================================================================
  Arduino firmware: prosthetic_hand.ino  (simple open/close)

  Automatically sends closed (0°) then open (180°) three times
  with 2-second holds. No input needed — just run and watch.
  Good for confirming all 5 servos respond without touching anything.

  Usage:
    python test_servo_direct.py
    python test_servo_direct.py /dev/cu.usbmodemXXXX
================================================================
"""
import sys
import time
import serial
import serial.tools.list_ports

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

print(f"Connecting to {PORT}...")
ser = serial.Serial(PORT, 9600, timeout=2)

print("Waiting 3s for Arduino startup sweep to finish...")
time.sleep(3)

for i in range(1, 4):
    print(f"\n--- Round {i}/3 ---")

    print("Sending 0° (closed)...")
    ser.write(bytes([0]))
    print("Holding 2s...")
    time.sleep(2)

    print("Sending 180° (open)...")
    ser.write(bytes([180]))
    print("Holding 2s...")
    time.sleep(2)

print("\nDone.")
ser.close()
