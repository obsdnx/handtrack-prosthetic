/*
 * Prosthetic Hand Controller — 2 Finger Servos
 *
 * Receives 2-byte packets from Python:
 *   [0xAA, finger_angle]
 *
 *   0°  = closed (finger curled into palm)
 *   90° = open   (finger extended)
 *
 * Both servos move to the same angle together.
 *
 * Wiring:
 *   Servo 1 signal → pin 9
 *   Servo 2 signal → pin 10
 */

#include <Servo.h>

const int BAUD_RATE   = 115200;
const byte START_BYTE = 0xAA;

Servo servo1;
Servo servo2;

void setup() {
    Serial.begin(BAUD_RATE);
    servo1.attach(9);
    servo2.attach(10);
    servo1.write(0);
    servo2.write(0);
    pinMode(13, OUTPUT);
}

void loop() {
    if (Serial.available() >= 2) {
        if (Serial.read() == START_BYTE) {
            byte angle = Serial.read();
            servo1.write(angle);
            servo2.write(angle);
            digitalWrite(13, HIGH);
            delay(50);
            digitalWrite(13, LOW);
        }
    }
}
