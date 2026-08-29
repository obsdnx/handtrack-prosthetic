"""
================================================================
  test_servo_interactive.py  —  INTERACTIVE ANGLE INPUT
================================================================
  Arduino firmware: prosthetic_hand.ino  (simple open/close)

  Type an angle (0–180) and press Enter. All 5 fingers move
  to that angle simultaneously. Good for manually checking
  servo range and verifying wiring.

  Usage:
    python test_servo_interactive.py
    python test_servo_interactive.py /dev/cu.usbmodemXXXX

  Input:
    0   → all fingers fully closed
    180 → all fingers fully open
    90  → midpoint

  Arduino echoes the angle back to confirm receipt.
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
print("Ready. Type an angle (0-180) and press Enter. Ctrl+C to quit.\n")

try:
    while True:
        raw = input("Angle: ").strip()
        if not raw:
            continue
        try:
            angle = int(raw)
        except ValueError:
            print("  Not a number, try again.")
            continue
        if not 0 <= angle <= 180:
            print("  Out of range (0-180), try again.")
            continue
        ser.write(bytes([angle]))
        echo = ser.read(1)
        if echo:
            print(f"  Sent {angle}° → Arduino confirmed {echo[0]}°")
        else:
            print(f"  Sent {angle}° → NO ECHO (Arduino not receiving)")
except KeyboardInterrupt:
    print("\nDone.")
finally:
    ser.close()
