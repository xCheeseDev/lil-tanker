# Wiring

## TB6612 -> Arduino Uno
| TB6612 | Uno | Notes |
|---|---|---|
| PWMA | 5 (PWM) | left motor speed |
| AIN1 | 7 | left motor direction |
| AIN2 | 8 | left motor direction |
| PWMB | 6 (PWM) | right motor speed |
| BIN1 | 9 | right motor direction |
| BIN2 | 10 | right motor direction |
| STBY | 4 | HIGH = driver enabled |
| VM | battery + | motor power (up to ~12V) |
| VCC | 5V | logic power |
| GND | GND | **common ground with everything** |
| AO1/AO2 | left motor | either polarity; flip AIN1/AIN2 in code if reversed |
| BO1/BO2 | right motor | same |

## HC-SR04 -> Uno
| HC-SR04 | Uno |
|---|---|
| VCC | 5V |
| TRIG | 11 |
| ECHO | 12 |
| GND | GND |

## Battery monitor
Battery+ -> voltage divider (e.g. 10k/10k) -> A0. Calibrate `DIVIDER_RATIO`
in `firmware/config.h` with a multimeter (see the comment there).

## Uno <-> Pi
USB A–B cable. The Pi powers the Uno's logic over USB; the motors keep
their own battery. Find the port on the Pi with `ls /dev/ttyACM*`.

All pin numbers live in `firmware/config.h` (copied from `config.h.example`),
so rewiring is a one-file change.
