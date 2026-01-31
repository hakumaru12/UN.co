#!/bin/bash

TARGET_SSID="BF-HSKK-2.4G"
MOMO_DIR="/home/haku12/momo"
TARGET_IP="192.168.11.2"
echo "=============================="
echo "Waiting for Wi-Fi - $TARGET_SSID"
echo "=============================="

while true; do
	SSID=$(iwgetid -r)

	[ "$SSID" = "$TARGET_SSID" ] && break
	sleep 2
done

IP_ADDR=$(hostname -I | awk '{print $1}')

echo "Wi-Fi connected!"

echo "=============================="
echo "SSID: $SSID"
echo "IP Address: $IP_ADDR"
echo "=============================="

echo "Starting streaming"
cd "$MOMO_DIR"
if ! tmux has-session -t momo 2>/dev/null; then
	tmux new-session -d -s momo "gst-launch-1.0 v4l2src device=/dev/video0 io-mode=2 ! image/jpeg,width=1280,height=720,framerate=30/1 ! jpegdec ! videoconvert ! openh264enc bitrate=6000000 complexity=0 ! rtph264pay pt=96 ! udpsink host=$TARGET_IP port=5000 sync=false
"
fi
echo "Streaming started!"
echo "Starting raspy.py (RC controll)"
python3 /home/haku12/raspi.py
