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
 *    Byte 1: thumb  angle  (inverted here: firmware writes 180-angle)
 *    Byte 2: index  angle
 *    Byte 3: middle angle
 *    Byte 4: ring   angle
 *    Byte 5: pinky  angle
 *
 *  Wiring:
 *    Thumb  signal → pin 12
 *    Index  signal → pin 11
 *    Middle signal → pin 10
 *    Ring   signal → pin  9
 *    Pinky  signal → pin 13
 *    All servos: red → external 5V, black/brown → external GND + Arduino GND
 * ============================================================
 */

#include <Servo.h>

const int BAUD_RATE = 9600;
const byte START_BYTE = 0xAA;

Servo servos[5];
const int PINS[5] = {12, 11, 10, 9, 13};  // thumb, index, middle, ring, pinky

void setup() {
    Serial.begin(BAUD_RATE);
    for (int i = 0; i < 5; i++) {
        servos[i].attach(PINS[i]);
        servos[i].write(i == 0 ? 0 : 160);  // thumb (index 0) reversed: 0 = open; max 160
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
        int out;
        if (i == 0) {
            out = 160 - angles[i];                          // thumb inverted
        } else if (i == 3) {
            out = angles[i] > 20 ? angles[i] - 20 : 0;     // ring offset by 20°
        } else {
            out = angles[i];
        }
        servos[i].write(constrain(out, 0, 160));
    }

    Serial.write(START_BYTE);  // echo start byte to confirm receipt
}
