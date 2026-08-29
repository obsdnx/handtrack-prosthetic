/*
 * ============================================================
 *  finger_control.ino  —  PER-FINGER CONTROL
 * ============================================================
 *
 *  USE WITH: test_finger_control.py  |  app.py (per-finger mode)
 *
 *  Each finger is controlled independently in one synchronised packet.
 *  Protocol: 6-byte packet
 *    Byte 0: 0xAA  (start byte — re-syncs if bytes are dropped)
 *    Byte 1: pinky  angle  (0=closed, 180=open)
 *    Byte 2: ring   angle
 *    Byte 3: middle angle
 *    Byte 4: index  angle
 *    Byte 5: thumb  angle  (inverted here: firmware writes 180-angle)
 *
 *  Wiring:
 *    Pinky  signal → pin  9
 *    Ring   signal → pin 10
 *    Middle signal → pin 11
 *    Index  signal → pin 12
 *    Thumb  signal → pin 13
 *    All servos: red → external 5V, black/brown → external GND + Arduino GND
 * ============================================================
 */

#include <Servo.h>

const int BAUD_RATE = 9600;
const byte START_BYTE = 0xAA;

Servo servos[5];
const int PINS[5] = {9, 10, 11, 12, 13};

void setup() {
    Serial.begin(BAUD_RATE);
    for (int i = 0; i < 5; i++) {
        servos[i].attach(PINS[i]);
        servos[i].write(i == 4 ? 0 : 180);  // thumb reversed: 0 = open
    }
}

void loop() {
    // Wait for start byte
    if (Serial.available() < 1) return;
    if (Serial.peek() != START_BYTE) {
        Serial.read();  // discard garbage byte and re-sync
        return;
    }

    // Need full 6-byte packet before acting
    if (Serial.available() < 6) return;

    Serial.read();  // consume 0xAA

    byte angles[5];
    for (int i = 0; i < 5; i++) {
        angles[i] = Serial.read();
    }

    // Write all servos simultaneously
    for (int i = 0; i < 5; i++) {
        int out = (i == 4) ? 180 - angles[i] : angles[i];  // thumb inverted
        servos[i].write(out);
    }

    Serial.write(START_BYTE);  // echo start byte to confirm receipt
}
