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
    print(f"  gripper={gripper:3d}°  wrist={wrist:3d}°")
    time.sleep(0.05)

try:
    print(">> Gripper open (45)")
    send(45, 22)
    time.sleep(1)

    print(">> Gripper close (0)")
    send(0, 22)
    time.sleep(1)

    print(">> Gripper mid (22)")
    send(22, 22)
    time.sleep(1)

    print(">> Wrist left (0)")
    send(22, 0)
    time.sleep(1)

    print(">> Wrist right (45)")
    send(22, 45)
    time.sleep(1)

    print(">> Wrist center (22)")
    send(22, 22)
    time.sleep(1)

    print("\nSweep complete. Did the servos move?")

finally:
    ser.close()
