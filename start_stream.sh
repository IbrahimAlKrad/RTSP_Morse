#!/bin/bash

# Start Kafka Stream
echo "🚀 Starting Kafka Stream..."

# Start Kafka
echo "📡 Starting Kafka..."
cd "$(dirname "$0")/SoundToMorse"
docker compose up -d
sleep 5

# Get Mac IP
MAC_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
echo ""
echo "✅ Kafka started!"
echo "📱 Use this WebSocket URL in your iPhone app:"
echo "   ws://$MAC_IP:8765"
echo ""

# Start WebSocket Bridge
echo "🌐 Starting WebSocket Bridge..."
cd "$(dirname "$0")/TextToSound/backend"
uv run websocket_bridge.py

