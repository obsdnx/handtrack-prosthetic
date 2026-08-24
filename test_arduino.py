"""
Quick test — sweeps gripper and wrist servos without camera.
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

def send(gripper, wrist):
    ser.write(bytes([START_BYTE, gripper, wrist]))
    print(f"  gripper={gripper:2d}°  wrist={wrist:2d}°")
    time.sleep(1)

try:
    print(">> Both closed (0°)")
    send(0, 0)

    print(">> Gripper open (45°)")
    send(45, 0)

    print(">> Gripper closed (0°)")
    send(0, 0)

    print(">> Wrist open (45°)")
    send(0, 45)

    print(">> Wrist closed (0°)")
    send(0, 0)

    print(">> Both open (45°)")
    send(45, 45)

    print(">> Both closed (0°)")
    send(0, 0)

    print("\nDid both servos move?")

finally:
    ser.close()
