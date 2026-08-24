/*
 * Prosthetic Hand Controller — Finger Servo
 *
 * Receives 2-byte packets from Python:
 *   [0xAA, finger_angle]
 *
 *   0°  = closed (anticlockwise, finger curled into palm)
 *   90° = open   (clockwise, finger extended)
 *
 * Wiring:
 *   Finger servo signal → pin 9
 */

#include <Servo.h>

const int BAUD_RATE    = 115200;
const byte START_BYTE  = 0xAA;
const int FINGER_PIN   = 9;

Servo fingerServo;

void setup() {
    Serial.begin(BAUD_RATE);
    fingerServo.attach(FINGER_PIN);
    fingerServo.write(0);  // start closed
}

void loop() {
    if (Serial.available() >= 2) {
        if (Serial.read() == START_BYTE) {
            byte angle = Serial.read();
            fingerServo.write(angle);
        }
    }
}
