/*
 * Prosthetic Hand Controller — 4 Servo Mirroring Mode
 *
 * Receives 5-byte packets from Python:
 *   [0xAA, thumb, index, middle, ring]
 *
 *   Each angle: 0 (curled/closed) to 45 (extended/open)
 *
 * Wiring:
 *   THUMB  servo signal → pin 6
 *   INDEX  servo signal → pin 7
 *   MIDDLE servo signal → pin 8
 *   RING   servo signal → pin 9
 */

#include <Servo.h>

const int BAUD_RATE   = 115200;
const byte START_BYTE = 0xAA;
const int NUM_SERVOS  = 4;

const int PINS[NUM_SERVOS] = {6, 7, 8, 9};  // thumb, index, middle, ring

Servo servos[NUM_SERVOS];

void setup() {
    Serial.begin(BAUD_RATE);
    for (int i = 0; i < NUM_SERVOS; i++) {
        servos[i].attach(PINS[i]);
        servos[i].write(0);  // start closed
    }
}

void loop() {
    if (Serial.available() >= 5) {
        if (Serial.read() == START_BYTE) {
            for (int i = 0; i < NUM_SERVOS; i++) {
                byte angle = Serial.read();
                servos[i].write(angle);
            }
        }
    }
}
