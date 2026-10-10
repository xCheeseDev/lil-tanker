"""Tools the AI can call. Each one maps to a real robot capability.

The model only ever sees the TOOLS schemas. execute_tool() runs them,
applying the safety governor (speed caps, distance caps) from config.
Calibration converts human units (meters, degrees) into the milliseconds
the Arduino firmware expects — tune these for your wheels/floor.
"""
from openai import OpenAI  # noqa: F401  (kept for type clarity)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "drive",
            "description": "Drive forward a short distance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "distance_m": {"type": "number", "description": "Meters to drive, 0.1 to 2.0"},
                    "speed_pct": {"type": "integer", "description": "Speed 10-100, default 40"},
                },
                "required": ["distance_m"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "back",
            "description": "Back up a short distance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "distance_m": {"type": "number", "description": "Meters, 0.1 to 1.0"},
                    "speed_pct": {"type": "integer", "description": "Speed 10-100, default 30"},
                },
                "required": ["distance_m"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "turn",
            "description": "Spin in place.",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {"type": "string", "enum": ["left", "right"]},
                    "degrees": {"type": "number", "description": "Degrees to turn, 15 to 180"},
                },
                "required": ["direction", "degrees"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stop",
            "description": "Stop all movement immediately.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sensors",
            "description": "Read the ultrasonic distance (cm) and battery voltage.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "speak",
            "description": "Say something out loud (shown on dashboard; TTS plugs in here).",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
    },
]


def execute_tool(name, args, link, cfg, say_fn):
    """Run one tool call. Returns a string the model sees as the result."""
    safety = cfg["safety"]
    calib = cfg["calibration"]
    max_speed = safety["max_speed_pct"]

    def clamp_speed(s):
        return max(10, min(int(s or 40), max_speed))

    if name == "drive":
        dist = max(0.05, min(float(args.get("distance_m", 0.2)), 2.0))
        ms = dist * calib["ms_per_meter"]
        reply = link.drive_ms(ms, clamp_speed(args.get("speed_pct")))
        return f"drove ~{dist:.2f}m: {reply}"

    if name == "back":
        dist = max(0.05, min(float(args.get("distance_m", 0.2)), 1.0))
        ms = dist * calib["ms_per_meter"]
        reply = link.back_ms(ms, clamp_speed(args.get("speed_pct", 30)))
        return f"backed up ~{dist:.2f}m: {reply}"

    if name == "turn":
        direction = args.get("direction", "left")
        deg = max(15.0, min(float(args.get("degrees", 90)), 180.0))
        ms = deg / 90.0 * calib["ms_per_90deg"]
        reply = link.turn_ms(direction, ms, clamp_speed(35))
        return f"turned {direction} ~{deg:.0f}deg: {reply}"

    if name == "stop":
        return link.stop()

    if name == "get_sensors":
        s = link.sensors()
        return f"distance_cm={s.get('dist_cm')} battery_v={s.get('batt_v')}"

    if name == "speak":
        text = str(args.get("text", ""))[:280]
        say_fn(text)  # dashboard log today, real TTS later
        return f"said: {text}"

    return f"ERR unknown tool: {name}"
