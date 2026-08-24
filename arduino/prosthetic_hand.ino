/*
 * Prosthetic Hand Controller — 2 Servo Mirroring Mode
 *
 * Receives 3-byte packets from Python:
 *   [0xAA, gripper_angle, wrist_angle]
 *
 *   Each angle: 0 (closed/curled) to 45 (open/extended)
 *
 * Wiring:
 *   GRIPPER servo signal → pin 9
 *   WRIST   servo signal → pin 10
 */

#include <Servo.h>

const int BAUD_RATE   = 115200;
const byte START_BYTE = 0xAA;
const int GRIPPER_PIN = 9;
const int WRIST_PIN   = 10;

Servo gripperServo;
Servo wristServo;

void setup() {
    Serial.begin(BAUD_RATE);
    gripperServo.attach(GRIPPER_PIN);
    wristServo.attach(WRIST_PIN);
    gripperServo.write(0);
    wristServo.write(0);
}

void loop() {
    if (Serial.available() >= 3) {
        if (Serial.read() == START_BYTE) {
            byte gripperAngle = Serial.read();
            byte wristAngle   = Serial.read();
            gripperServo.write(gripperAngle);
            wristServo.write(wristAngle);
        }
    }
}
