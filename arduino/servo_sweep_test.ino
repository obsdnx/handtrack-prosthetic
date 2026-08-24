/*
 * Servo sweep test with pause/resume.
 * Sweeps both servos: 0 -> 45 -> 90 -> 45 -> 0, repeat.
 * Press button on pin 2 to pause/resume.
 *
 * Wiring (optional button):
 *   One side of button → pin 2
 *   Other side         → GND
 */
#include <Servo.h>

Servo servo1;
Servo servo2;

const int BUTTON_PIN = 2;
bool paused = false;
bool lastButtonState = HIGH;

void setup() {
    servo1.attach(9);
    servo2.attach(10);
    pinMode(BUTTON_PIN, INPUT_PULLUP);
}

void checkButton() {
    bool buttonState = digitalRead(BUTTON_PIN);
    if (buttonState == LOW && lastButtonState == HIGH) {
        paused = !paused;
        delay(50);  // debounce
    }
    lastButtonState = buttonState;
}

void moveTo(int angle) {
    while (paused) {
        checkButton();
        delay(10);
    }
    servo1.write(angle);
    servo2.write(angle);
}

void loop() {
    checkButton();
    moveTo(0);   delay(1000);
    moveTo(45);  delay(1000);
    moveTo(90);  delay(1000);
    moveTo(45);  delay(1000);
    moveTo(0);   delay(1000);
}
