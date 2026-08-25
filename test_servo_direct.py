"""
Direct servo test — no camera, no handshake, just forces servo to 90° then 0°.
Run: python test_servo_direct.py
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

    print("Sending 90° (closed)...")
    for _ in range(10):
        ser.write(bytes([0xAA, 90]))
        time.sleep(0.1)
    print("Holding 2s...")
    time.sleep(2)

    print("Sending 0° (open)...")
    for _ in range(10):
        ser.write(bytes([0xAA, 0]))
        time.sleep(0.1)
    print("Holding 2s...")
    time.sleep(2)

print("\nDone.")
ser.close()
