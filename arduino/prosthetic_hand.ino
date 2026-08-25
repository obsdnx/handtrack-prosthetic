/*
 * Prosthetic Hand Controller — 2 Finger Servos
 *
 * Receives a single byte from Python: the servo angle (0–90).
 *   0°  = open   (finger extended)
 *   90° = closed (finger curled into palm)
 *
 * Both servos move to the same angle together.
 *
 * Wiring:
 *   Servo 1 signal → pin 9
 *   Servo 2 signal → pin 10
 *   Both servos: red → 5V, black/brown → GND
 *
 * Notes:
 *   - Thumb opens anti-clockwise, closes clockwise
 *   - 0° = open, 90° = closed
 */

#include <Servo.h>

const int BAUD_RATE = 9600;

Servo servo1;
Servo servo2;

void setup() {
    Serial.begin(BAUD_RATE);
    servo1.attach(9);
    servo2.attach(10);
    pinMode(13, OUTPUT);

    // Startup sweep — confirms servos are wired and working
    servo1.write(0);  servo2.write(0);  delay(700);
    servo1.write(90); servo2.write(90); delay(700);
    servo1.write(0);  servo2.write(0);  delay(500);
}

void loop() {
    if (Serial.available()) {
        byte angle = Serial.read();
        servo1.write(angle);
        servo2.write(angle);
        digitalWrite(13, HIGH);
        delay(200);
        digitalWrite(13, LOW);
    }
}
