/*
 * Servo diagnostic — no serial needed.
 * Sweeps gripper (pin 9) and wrist (pin 10) automatically.
 * If servos move with this sketch, wiring is correct.
 */
#include <Servo.h>

Servo gripperServo;
Servo wristServo;

void setup() {
    gripperServo.attach(9);
    wristServo.attach(10);
}

void loop() {
    // Open gripper
    gripperServo.write(0);
    delay(1000);

    // Close gripper
    gripperServo.write(180);
    delay(1000);

    // Wrist left
    wristServo.write(0);
    delay(1000);

    // Wrist right
    wristServo.write(180);
    delay(1000);

    // Center both
    gripperServo.write(90);
    wristServo.write(90);
    delay(1000);
}
