"""Serial link between the Pi and the Arduino Uno.

Speaks the plain-text protocol from firmware/robot.ino over USB serial.
Every method is synchronous with a timeout; a threading lock makes it
safe to call from the chat loop and the web dashboard at the same time.
"""
import threading
import serial


class ArduinoLink:
    def __init__(self, port, baud=115200, timeout=1.0):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self._ser = None
        self._lock = threading.Lock()

    def connect(self):
        self._ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
        # Uno resets on serial open; give it a moment and drain the banner.
        import time
        time.sleep(2.0)
        self._ser.reset_input_buffer()
        return self.ping()

    def close(self):
        if self._ser:
            try:
                self.stop()
                self._ser.close()
            except Exception:
                pass
            self._ser = None

    @property
    def connected(self):
        return self._ser is not None and self._ser.is_open

    def _cmd(self, line):
        """Send a line, return the first reply line (without newline)."""
        with self._lock:
            self._ser.reset_input_buffer()
            self._ser.write((line + "\n").encode())
            self._ser.flush()
            # Read until we get OK / ERR / PONG / SENSORS / EVENT.
            # EVENT lines can arrive on their own; skip past them here.
            import time
            deadline = time.time() + self.timeout
            while time.time() < deadline:
                raw = self._ser.readline()
                if not raw:
                    continue
                text = raw.decode(errors="replace").strip()
                if text.startswith("EVENT"):
                    continue
                return text
            raise TimeoutError(f"no reply to: {line}")

    # ---- high-level API used by tools.py ----
    def drive_ms(self, ms, speed):
        return self._cmd(f"DRIVE {int(ms)} {int(speed)}")

    def back_ms(self, ms, speed):
        return self._cmd(f"BACK {int(ms)} {int(speed)}")

    def turn_ms(self, direction, ms, speed):
        cmd = "TURNL" if direction == "left" else "TURNR"
        return self._cmd(f"{cmd} {int(ms)} {int(speed)}")

    def stop(self):
        try:
            return self._cmd("STOP")
        except Exception:
            return "ERR link down"

    def ping(self):
        try:
            return self._cmd("PING") == "PONG"
        except Exception:
            return False

    def sensors(self):
        """Return {'dist_cm': int, 'batt_v': float}."""
        reply = self._cmd("SENSORS")
        # SENSORS dist_cm=42 batt_v=7.8
        data = {}
        for part in reply.split()[1:]:
            if "=" in part:
                k, v = part.split("=", 1)
                try:
                    data[k] = float(v) if "." in v else int(v)
                except ValueError:
                    data[k] = v
        return data
