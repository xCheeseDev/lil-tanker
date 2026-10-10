# Bill of materials

Approximate prices in CAD; clones are fine everywhere except the Pi.

## Compute
| Part | Notes | ~CAD |
|---|---|---|
| Arduino Uno R3 (clone ok) | the muscle | $15–25 |
| Raspberry Pi 4/5, 2GB+ | the brain; a Pi Zero 2 W works if the AI runs elsewhere | $25–100 |
| MicroSD 32GB | Pi OS | $12 |

## Drive
| Part | Notes | ~CAD |
|---|---|---|
| TB6612 motor driver breakout | more efficient than the old L298N | $8 |
| 2x TT gear motors + wheels | the classic yellow ones | $10 |
| Caster wheel | third point of contact | $3 |
| Chassis | acrylic 2WD kit, or 3D print / cut your own | $12 |

## Sense & power
| Part | Notes | ~CAD |
|---|---|---|
| HC-SR04 ultrasonic sensor | obstacle detection | $4 |
| Battery pack | 2x 18650 holder **or** USB power bank with 5V+ motor supply | $15 |
| Jumper wires, USB A–B cable | Uno to Pi link | $8 |

**Total: roughly $60–120 CAD** depending on what you already own.

## Power warning
Power the motors from a **separate** supply from the Uno's logic if you can
(motor noise browns out the Uno and causes phantom resets). Always connect
the grounds together. The TB6612's VM pin takes the motor battery; VCC takes 5V logic.
