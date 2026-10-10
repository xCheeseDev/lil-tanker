/*
 * lil-tanker firmware — Arduino Uno
 *
 * The Uno is the muscle. It does NOT do AI. It:
 *  - drives two motors through a TB6612 driver (differential drive)
 *  - reads an HC-SR04 ultrasonic sensor for obstacle detection
 *  - reports battery voltage
 *  - talks to the Raspberry Pi over USB serial using plain text lines
 *
 * Safety is enforced HERE, not in the AI:
 *  - WATCHDOG: if the Pi goes silent, motors stop.
 *  - OBSTACLE: forward motion hard-stops inside STOP_DIST_CM.
 * The AI can request movement, but it cannot override either of these.
 *
 * Serial protocol (115200 baud, one command per line):
 *   DRIVE <ms> <speed>    forward,  e.g. DRIVE 1000 60
 *   BACK  <ms> <speed>    backward
 *   TURNL <ms> <speed>    spin left in place
 *   TURNR <ms> <speed>    spin right in place
 *   STOP                 stop immediately
 *   SENSORS              -> SENSORS dist_cm=NN batt_v=X.X
 *   PING                 -> PONG
 * Replies: OK, ERR <reason>, EVENT obstacle
 *
 * Copy config.h.example to config.h and adjust pins/thresholds first.
 */
#include "config.h"

// ---- movement state ----
struct Move {
  bool active = false;
  unsigned long endAt = 0;
  bool forward = false;  // true only for DRIVE (used by obstacle check)
};
Move currentMove;

unsigned long lastRx = 0;      // last time we heard from the Pi
unsigned long lastPing = 0;    // last ultrasonic ping
int lastDistCm = 999;

// ---- motor helpers (TB6612) ----
void motorWrite(int pwmPin, int in1, int in2, int speed) {
  // speed: -100..100
  speed = constrain(speed, -100, 100);
  if (speed > 0) {
    digitalWrite(in1, HIGH); digitalWrite(in2, LOW);
  } else if (speed < 0) {
    digitalWrite(in1, LOW); digitalWrite(in2, HIGH);
  } else {
    digitalWrite(in1, LOW); digitalWrite(in2, LOW);  // brake
  }
  analogWrite(pwmPin, map(abs(speed), 0, 100, 0, 255));
}

void motorsStop() {
  motorWrite(PWMA, AIN1, AIN2, 0);
  motorWrite(PWMB, BIN1, BIN2, 0);
  currentMove.active = false;
}

void startMove(bool fwd, int leftSpeed, int rightSpeed, unsigned long ms) {
  motorWrite(PWMA, AIN1, AIN2, leftSpeed);
  motorWrite(PWMB, BIN1, BIN2, rightSpeed);
  currentMove.active = true;
  currentMove.forward = fwd;
  currentMove.endAt = millis() + ms;
}

// ---- sensors ----
int readUltrasonicCm() {
  digitalWrite(TRIG_PIN, LOW); delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH); delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long us = pulseIn(ECHO_PIN, HIGH, 30000);  // 30ms timeout
  if (us == 0) return 999;
  return (int)(us / 58);
}

float readBatteryV() {
  int raw = analogRead(BATT_PIN);
  // ADC 0..1023 -> 0..5V, scaled by the voltage divider. Calibrate DIVIDER_RATIO.
  return raw * (5.0 / 1023.0) * DIVIDER_RATIO;
}

// ---- command handling ----
void handleLine(String line) {
  line.trim();
  if (line.length() == 0) return;
  lastRx = millis();

  if (line == "STOP")            { motorsStop(); Serial.println("OK"); return; }
  if (line == "PING")            { Serial.println("PONG"); return; }
  if (line == "SENSORS") {
    Serial.print("SENSORS dist_cm=");
    Serial.print(lastDistCm);
    Serial.print(" batt_v=");
    Serial.println(readBatteryV(), 1);
    return;
  }

  // DRIVE <ms> <speed> | BACK <ms> <speed> | TURNL <ms> <speed> | TURNR <ms> <speed>
  char cmd[6]; long ms; int speed;
  if (sscanf(line.c_str(), "%5s %ld %d", cmd, &ms, &speed) == 3) {
    String c = String(cmd);
    ms = constrain(ms, 0, MAX_MOVE_MS);
    speed = constrain(abs(speed), 0, MAX_SPEED_PCT);
    if (c == "DRIVE")      { startMove(true, speed, speed, ms); }
    else if (c == "BACK")  { startMove(false, -speed, -speed, ms); }
    else if (c == "TURNL") { startMove(false, -speed, speed, ms); }
    else if (c == "TURNR") { startMove(false, speed, -speed, ms); }
    else { Serial.println("ERR unknown command"); return; }
    Serial.println("OK");
    return;
  }
  Serial.println("ERR bad format");
}

void setup() {
  Serial.begin(115200);
  pinMode(PWMA, OUTPUT); pinMode(AIN1, OUTPUT); pinMode(AIN2, OUTPUT);
  pinMode(PWMB, OUTPUT); pinMode(BIN1, OUTPUT); pinMode(BIN2, OUTPUT);
  pinMode(STBY_PIN, OUTPUT);
  digitalWrite(STBY_PIN, HIGH);  // enable driver
  pinMode(TRIG_PIN, OUTPUT); pinMode(ECHO_PIN, INPUT);
  motorsStop();
  lastRx = millis();
  Serial.println("READY lil-tanker");
}

void loop() {
  // 1. incoming commands
  while (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    handleLine(line);
  }

  unsigned long now = millis();

  // 2. timed moves expire on their own
  if (currentMove.active && (long)(now - currentMove.endAt) >= 0) {
    motorsStop();
  }

  // 3. watchdog: Pi went silent with motors running and no timed move -> stop
  if (!currentMove.active && (now - lastRx > WATCHDOG_MS)) {
    motorsStop();  // cheap to call repeatedly; keeps us safe
    lastRx = now;  // don't spam; re-arm
  }

  // 4. obstacle check (throttled; ultrasonic pings are slow)
  if (now - lastPing > 120) {
    lastPing = now;
    lastDistCm = readUltrasonicCm();
    if (currentMove.active && currentMove.forward && lastDistCm < STOP_DIST_CM) {
      motorsStop();
      Serial.println("EVENT obstacle");
    }
  }
}
