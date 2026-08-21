/*
 * Prosthetic Hand Controller
 *
 * Receives single-byte commands from Python over USB serial
 * and drives servos accordingly.
 *
 * Commands:
 *   0x01  OPEN_GRIPPER
 *   0x02  CLOSE_GRIPPER
 *   0x03  PINCH
 *   0x04  ROTATE_CW
 *   0x05  ROTATE_CCW
 *   0x06  HOLD
 *   0xFF  PING — echo back 0xFF
 *
 * Wiring (adjust pins to match your board):
 *   GRIPPER_SERVO  → pin 9
 *   WRIST_SERVO    → pin 10
 */

#include <Servo.h>

const int BAUD_RATE     = 9600;
const int GRIPPER_PIN   = 9;
const int WRIST_PIN     = 10;

// Servo positions (degrees) — tune to your mechanism
const int GRIPPER_OPEN  = 0;
const int GRIPPER_CLOSE = 180;
const int GRIPPER_PINCH = 90;
const int WRIST_CENTER  = 90;
const int WRIST_CW      = 180;
const int WRIST_CCW     = 0;

Servo gripperServo;
Servo wristServo;

void setup() {
    Serial.begin(BAUD_RATE);
    gripperServo.attach(GRIPPER_PIN);
    wristServo.attach(WRIST_PIN);

    // Start in neutral position
    gripperServo.write(GRIPPER_OPEN);
    wristServo.write(WRIST_CENTER);
}

void loop() {
    if (Serial.available() > 0) {
        byte cmd = Serial.read();
        handleCommand(cmd);
    }
}

void handleCommand(byte cmd) {
    switch (cmd) {
        case 0x01:  // OPEN_GRIPPER
            gripperServo.write(GRIPPER_OPEN);
            break;
        case 0x02:  // CLOSE_GRIPPER
            gripperServo.write(GRIPPER_CLOSE);
            break;
        case 0x03:  // PINCH
            gripperServo.write(GRIPPER_PINCH);
            break;
        case 0x04:  // ROTATE_CW
            wristServo.write(WRIST_CW);
            break;
        case 0x05:  // ROTATE_CCW
            wristServo.write(WRIST_CCW);
            break;
        case 0x06:  // HOLD
            // No movement
            break;
        case 0xFF:  // PING
            Serial.write(0xFF);
            break;
        default:
            break;
    }
}
