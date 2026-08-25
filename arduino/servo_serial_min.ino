/*
 * Minimum serial servo test.
 * Receives a single byte = angle (0-90), moves both servos.
 * No start byte, no framing.
 */
#include <Servo.h>

Servo s1;
Servo s2;

void setup() {
    Serial.begin(9600);
    s1.attach(9);
    s2.attach(10);

    // Confirm servos work
    s1.write(0);  s2.write(0);  delay(1000);
    s1.write(90); s2.write(90); delay(1000);
    s1.write(0);  s2.write(0);  delay(500);
}

void loop() {
    if (Serial.available()) {
        byte angle = Serial.read();
        s1.write(angle);
        s2.write(angle);
        digitalWrite(13, HIGH);
        delay(200);
        digitalWrite(13, LOW);
    }
}
