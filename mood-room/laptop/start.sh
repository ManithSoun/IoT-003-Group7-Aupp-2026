#!/bin/bash
echo "Setting up routes..."
sudo route add -net 192.168.18.0/24 -interface en0 2>/dev/null || true
sudo ifconfig utun0 down 2>/dev/null || true
sudo ifconfig utun1 down 2>/dev/null || true
sudo ifconfig utun2 down 2>/dev/null || true
sudo ifconfig utun3 down 2>/dev/null || true
sudo ifconfig utun4 down 2>/dev/null || true
sudo ifconfig utun5 down 2>/dev/null || true
sudo ifconfig utun6 down 2>/dev/null || true
sudo ifconfig utun7 down 2>/dev/null || true

echo "Starting Flask server..."
cd ~/IoT-003-Group7-Aupp-2026/mood-room/laptop && python3 server.py &
sleep 5  # wait for server to start

echo "Starting webcam..."
python3 webcam.py
