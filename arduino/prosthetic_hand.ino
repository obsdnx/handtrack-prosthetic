/*
 * Prosthetic Hand Controller — Continuous Mirroring Mode
 *
 * Receives 3-byte packets from Python:
 *   [0xAA, gripper_angle, wrist_angle]
 *
 *   0xAA          = start byte
 *   gripper_angle = 0 (closed) to 180 (open)
 *   wrist_angle   = 0 to 180
 *
 * Wiring:
 *   GRIPPER_SERVO → pin 9
 *   WRIST_SERVO   → pin 10
 */

#include <Servo.h>

const int BAUD_RATE   = 115200;
const int GRIPPER_PIN = 9;
const int WRIST_PIN   = 10;
const byte START_BYTE = 0xAA;

Servo gripperServo;
Servo wristServo;

void setup() {
    Serial.begin(BAUD_RATE);
    gripperServo.attach(GRIPPER_PIN);
    wristServo.attach(WRIST_PIN);
    gripperServo.write(90);
    wristServo.write(90);
}

void loop() {
    // Wait for start byte
    if (Serial.available() >= 3) {
        if (Serial.read() == START_BYTE) {
            byte gripperAngle = Serial.read();
            byte wristAngle   = Serial.read();
            gripperServo.write(gripperAngle);
            wristServo.write(wristAngle);
        }
    }
}
