"""
Quick test — sweeps all 4 servos without camera.
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

def send(thumb, index, middle, ring):
    ser.write(bytes([START_BYTE, thumb, index, middle, ring]))
    print(f"  thumb={thumb:2d}°  index={index:2d}°  middle={middle:2d}°  ring={ring:2d}°")
    time.sleep(0.8)

try:
    print(">> All closed (0°)")
    send(0, 0, 0, 0)

    print(">> All open (45°)")
    send(45, 45, 45, 45)

    print(">> Thumb only open")
    send(45, 0, 0, 0)

    print(">> Index only open")
    send(0, 45, 0, 0)

    print(">> Middle only open")
    send(0, 0, 45, 0)

    print(">> Ring only open")
    send(0, 0, 0, 45)

    print(">> All closed")
    send(0, 0, 0, 0)

    print("\nDid each servo move independently?")

finally:
    ser.close()
