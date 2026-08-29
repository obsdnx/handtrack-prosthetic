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

Servo servo1;
Servo servo2;
Servo servo3;
Servo servo4;
Servo servo5;

void writeAll(int angle) {
    servo1.write(angle);
    servo2.write(angle);
    servo3.write(angle);
    servo4.write(angle);
    servo5.write(angle);
}

void setup() {
    Serial.begin(BAUD_RATE);
    servo1.attach(9);
    servo2.attach(10);
    servo3.attach(11);
    servo4.attach(12);
    servo5.attach(13);

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
