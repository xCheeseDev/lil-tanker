# Pi setup

## 1. Flash Raspberry Pi OS
Use Raspberry Pi Imager, Lite is fine (no desktop needed).

## 2. Find the Arduino
Plug the Uno into the Pi over USB, then:
```sh
ls /dev/ttyACM*
```
Usually `/dev/ttyACM0`. Put it in `brain/config.yaml` under `robot.serial_port`.

Add your user to the serial group so you don't need sudo:
```sh
sudo usermod -a -G dialout $USER
# log out and back in
```

## 3. Install the brain
```sh
cd brain
pip install -r requirements.txt
python3 brain.py   # creates config.yaml from the example on first run
```
Edit `config.yaml`: pick your AI provider. If Ollama runs on your main PC,
set `base_url: http://<pc-ip>:11434/v1` — the Pi just relays.

## 4. Flash the firmware (from any PC with Arduino IDE)
1. Open `firmware/robot.ino`.
2. Copy `firmware/config.h.example` to `firmware/config.h`, adjust pins if needed.
3. Select board "Arduino Uno", upload.

Test it without the Pi first: open Serial Monitor at 115200, type `PING`
(expect `PONG`), `SENSORS`, then `DRIVE 1000 40` with the wheels off the ground.

## 5. Run as a service (optional)
```ini
# /etc/systemd/system/liltanker.service
[Unit]
Description=lil-tanker brain
After=network.target

[Service]
WorkingDirectory=/home/pi/lil-tanker/brain
ExecStart=/usr/bin/python3 brain.py
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```
```sh
sudo systemctl enable --now liltanker
```
