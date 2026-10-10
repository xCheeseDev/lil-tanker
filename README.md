# lil-tanker

A wheeled robot companion for your floor or desk. Arduino drives, Raspberry Pi thinks — connect any AI via API, including local models.

## Architecture

```
 you talk
    │
    ▼
┌─────────────┐   OpenAI-compatible API    ┌──────────────┐
│ brain.py    │ ◄────────────────────────── │ Ollama /     │
│ (Pi)        │   chat + tool calls         │ LM Studio /  │
│             │                             │ OpenAI / …   │
│ tools.py    │                             └──────────────┘
│ arduino_    │   USB serial (plain text)
│  link.py    │◄────────────────────────┐
└─────────────┘                         │
                              ┌─────────▼─────────┐
                              │ robot.ino (Uno)   │
                              │ motors, ultrasonic│
                              │ watchdog, obstacle│
                              │ hard-stop         │
                              └───────────────────┘
```

**The split is the whole design:** the Uno handles real-time motor control
and safety; the Pi handles conversation and decisions. Swap AI providers with
one line in `config.yaml` — no reflashing. If the Pi dies or the AI says
something dumb, the firmware's watchdog and ultrasonic hard-stop keep the
robot safe. The AI can *request* movement; it cannot *override* physics.

## Quickstart

1. **Wire it** — see `docs/wiring.md` and `docs/BOM.md` (~$60–120 CAD in parts).
2. **Flash the Uno** — open `firmware/robot.ino` in Arduino IDE (copy
   `config.h.example` → `config.h` first), upload.
3. **Set up the Pi** — see `docs/pi_setup.md`.
4. **Configure the AI** — `brain/config.yaml`: point `base_url` at Ollama,
   LM Studio, OpenAI, or anything OpenAI-compatible.
5. **Run it**:
   ```sh
   cd brain && pip install -r requirements.txt && python3 brain.py
   ```
6. Open the dashboard at `http://<pi-ip>:8080` — telemetry, manual drive pad,
   and everything the tanker says.

## What the AI can do

Through tool calls: `drive` / `back` (meters), `turn` (degrees),
`stop`, `get_sensors` (ultrasonic cm + battery V), `speak` (dashboard log;
real TTS plugs into `tools.py`). Calibration (`ms_per_meter`,
`ms_per_90deg`) lives in `config.yaml` — time your bot once and set it.

## Safety

- Firmware-enforced: 800ms command watchdog, ultrasonic hard-stop inside
  20cm while driving forward, per-command speed/duration caps.
- Brain-enforced: configurable speed cap, distance cap, refuses to run
  without a live Arduino link.
- Nothing here is a weapon; keep speeds low around pets, kids, and stairs.

## Status

Scaffold / v0.1. The protocol, tools, and safety layers are in place but
untested against real hardware — expected first tasks: calibrate
`ms_per_meter` / `ms_per_90deg`, verify the ultrasonic stop distance,
plug in real TTS for `speak`.
