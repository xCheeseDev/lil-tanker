"""lil-tanker brain — runs on the Raspberry Pi.

Loop: read what you say -> send it + tool schemas to the AI ->
execute any tool calls against the Arduino -> show the reply.

The AI provider is OpenAI-compatible, so this works with OpenAI,
Ollama (local), LM Studio (local), or anything else speaking the
chat-completions format. Switching is one line in config.yaml.

Safety: the firmware enforces the hard limits (watchdog, obstacle stop).
This layer adds the soft limits (speed/distance caps from config) and
refuses to run without a live Arduino link.
"""
import json
import shutil
import sys

import yaml
from openai import OpenAI

from arduino_link import ArduinoLink
from tools import TOOLS, execute_tool
from web_server import start_dashboard

SYSTEM_PROMPT = """You are the mind of lil-tanker, a small wheeled robot companion.
You live on a Raspberry Pi and drive an Arduino Uno over USB serial.

Your tools: drive (meters), back (meters), turn (left/right, degrees),
stop, get_sensors (ultrasonic cm + battery volts), speak (text).

Rules:
- Keep movements small and check get_sensors before driving into unknown space.
- Never invent sensor readings; call get_sensors if you need them.
- If the battery is under 6.5V, say so and stop driving.
- Be brief and a little charming. You are a desk/floor companion, not a lecture bot.
"""


def load_config():
    try:
        with open("config.yaml") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        shutil.copy("config.example.yaml", "config.yaml")
        print("Created config.yaml from the example — edit it, then run again.")
        sys.exit(1)


def main():
    cfg = load_config()
    ai = cfg["ai"]

    client = OpenAI(base_url=ai["base_url"], api_key=ai.get("api_key", "not-needed"))
    model = ai["model"]

    link = ArduinoLink(cfg["robot"]["serial_port"], cfg["robot"].get("baud", 115200))
    print(f"Connecting to Arduino on {link.port} ...")
    if not link.connect():
        print("Could not reach the Arduino. Check the port in config.yaml and that the firmware is flashed.")
        sys.exit(1)
    print("Arduino link up.")

    spoken_log = []
    def say_fn(text):
        spoken_log.append(text)
        print(f"[tanker says] {text}")

    start_dashboard(link, spoken_log, cfg["web"]["port"])
    print(f"Dashboard at http://<pi-ip>:{cfg['web']['port']}")
    print("Type to chat. 'quit' exits.\n")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    try:
        while True:
            user = input("you> ").strip()
            if user.lower() in ("quit", "exit"):
                break
            if not user:
                continue
            messages.append({"role": "user", "content": user})

            # Let the model make tool calls until it just answers.
            for _ in range(5):  # cap tool-call rounds per message
                resp = client.chat.completions.create(
                    model=model, messages=messages, tools=TOOLS
                )
                msg = resp.choices[0].message
                messages.append(msg)
                if not msg.tool_calls:
                    print("tanker>", msg.content or "")
                    break
                for call in msg.tool_calls:
                    args = json.loads(call.function.arguments or "{}")
                    result = execute_tool(call.function.name, args, link, cfg, say_fn)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": result,
                    })
    except KeyboardInterrupt:
        pass
    finally:
        link.close()
        print("\nbye.")


if __name__ == "__main__":
    main()
