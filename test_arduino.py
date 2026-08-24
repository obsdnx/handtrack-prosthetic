"""
Quick test — sweeps finger servo without camera.
Run: python test_arduino.py /dev/cu.usbmodem101
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
    print("No Arduino found. Plug it in or run: python test_arduino.py /dev/cu.xxx")
    sys.exit(1)
print(f"Found Arduino at: {PORT}")
BAUD = 115200
START_BYTE = 0xAA

print(f"Connecting to {PORT} @ {BAUD}...")
ser = serial.Serial(PORT, BAUD, timeout=5)
print("Waiting for Arduino ready signal...")
deadline = time.time() + 10
while time.time() < deadline:
    if ser.in_waiting:
        byte = ser.read(1)
        if byte == b'\xBB':
            break
ser.timeout = 1
print("Connected. Starting sweep...\n")

def send(angle):
    ser.write(bytes([START_BYTE, angle]))
    print(f"  finger={angle:3d}°")

try:
    print(">> Closed (0°)")
    send(0)

    print(">> Half open (45°)")
    send(45)

    print(">> Fully open (90°)")
    send(90)

    print(">> Half open (45°)")
    send(45)

    print(">> Closed (0°)")
    send(0)

    print("\nDid the servo move from 0° to 90°?")

finally:
    ser.close()
