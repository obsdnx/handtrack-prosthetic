/*
 * ============================================================
 *  prosthetic_hand.ino  —  SIMPLE OPEN/CLOSE
 * ============================================================
 *
 *  USE WITH: test_servo_interactive.py  |  test_servo_direct.py
 *            test_servo_min.py          |  app.py (simple mode)
 *
 *  All 5 servos move to the same angle together.
 *  Receives one byte per command: 0 = closed, 180 = open.
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

Servo thumb;
Servo index;
Servo middle;
Servo ring;
Servo pinky;

void writeAll(int angle) {
    thumb.write(180 - angle);  // mechanically reversed
    index.write(angle);
    middle.write(angle);
    ring.write(angle);
    pinky.write(angle);
}

void setup() {
    Serial.begin(BAUD_RATE);
    thumb.attach(12);
    index.attach(11);
    middle.attach(10);
    ring.attach(9);
    pinky.attach(13);

    // Startup sweep — confirms all servos are wired and working
    writeAll(180); delay(700);
    writeAll(0);   delay(700);
    writeAll(180); delay(500);
}

void loop() {
    if (Serial.available()) {
        byte angle = Serial.read();
        writeAll(angle);
        Serial.write(angle);  // echo back so Python can confirm receipt
    }
}
