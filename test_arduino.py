"""
Quick test — sweeps finger servo without camera.
Run: python test_arduino.py /dev/cu.usbmodem1101
"""
import sys
import time
import serial

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/cu.usbmodem1101"
BAUD = 115200
START_BYTE = 0xAA

print(f"Connecting to {PORT} @ {BAUD}...")
ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)
print("Connected. Starting sweep...\n")

def send(angle):
    ser.write(bytes([START_BYTE, angle]))
    print(f"  finger={angle:3d}°")
    time.sleep(1)

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
