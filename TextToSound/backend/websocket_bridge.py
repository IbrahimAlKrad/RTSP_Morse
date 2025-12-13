#!/usr/bin/env python3
"""
WebSocket Bridge for Kafka -> iOS
Connects to Kafka and pushes messages to connected WebSocket clients in real-time.
"""

import asyncio
import json
import logging
from typing import Set
from confluent_kafka import Consumer, KafkaError
import websockets
from websockets import ServerConnection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
KAFKA_GROUP_ID = 'websocket-bridge'
TOPICS = ['morse_output', 'text_input', 'backend_health']
WEBSOCKET_HOST = '0.0.0.0'  # Listen on all interfaces
WEBSOCKET_PORT = 8765

# Connected WebSocket clients
connected_clients: Set[ServerConnection] = set()


async def broadcast_message(message: str, topic: str):
    """Send message to all connected WebSocket clients"""
    if not connected_clients:
        return
    
    payload = json.dumps({
        "topic": topic,
        "message": message,
        "timestamp": asyncio.get_event_loop().time()
    })
    
    # Send to all connected clients
    disconnected = set()
    for client in connected_clients:
        try:
            await client.send(payload)
        except websockets.exceptions.ConnectionClosed:
            disconnected.add(client)
    
    # Remove disconnected clients
    connected_clients.difference_update(disconnected)


async def kafka_consumer():
    """Consume messages from Kafka and broadcast to WebSocket clients"""
    conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': KAFKA_GROUP_ID,
        'auto.offset.reset': 'latest',  # Only get new messages
        'enable.auto.commit': True
    }
    
    consumer = Consumer(conf)
    consumer.subscribe(TOPICS)
    logger.info(f"📡 Kafka consumer started, subscribed to: {TOPICS}")
    
    try:
        while True:
            msg = consumer.poll(timeout=0.1)  # Non-blocking poll
            
            if msg is None:
                await asyncio.sleep(0.01)  # Yield to other tasks
                continue
            
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error(f"Kafka error: {msg.error()}")
                    continue
            
            # Got a message!
            topic = msg.topic()
            value = msg.value().decode('utf-8')
            logger.info(f"📨 Received from {topic}: {value[:50]}...")
            
            # Broadcast to all WebSocket clients
            await broadcast_message(value, topic)
            
    except asyncio.CancelledError:
        logger.info("Kafka consumer cancelled")
    finally:
        consumer.close()
        logger.info("Kafka consumer closed")


async def websocket_handler(websocket: ServerConnection):
    """Handle WebSocket connections"""
    client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
    logger.info(f"🔌 New WebSocket connection from {client_ip}")
    
    connected_clients.add(websocket)
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "connected",
            "message": "Connected to Kafka WebSocket Bridge",
            "topics": TOPICS
        }))
        
        # Handle incoming messages from client (for sending to Kafka)
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"📤 Received from client: {data}")
                # You could add logic here to produce messages to Kafka
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from client: {message}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"🔌 WebSocket connection closed from {client_ip}")
    finally:
        connected_clients.discard(websocket)


async def main():
    """Main entry point"""
    logger.info("=" * 50)
    logger.info("🚀 Kafka WebSocket Bridge Starting...")
    logger.info(f"📡 Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"🌐 WebSocket: ws://0.0.0.0:{WEBSOCKET_PORT}")
    logger.info(f"📋 Topics: {TOPICS}")
    logger.info("=" * 50)
    
    # Start WebSocket server
    server = await websockets.serve(
        websocket_handler,
        WEBSOCKET_HOST,
        WEBSOCKET_PORT
    )
    
    logger.info(f"✅ WebSocket server running on ws://0.0.0.0:{WEBSOCKET_PORT}")
    
    # Run Kafka consumer in background
    kafka_task = asyncio.create_task(kafka_consumer())
    
    try:
        # Keep running
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutting down...")
    finally:
        kafka_task.cancel()
        server.close()
        await server.wait_closed()


if __name__ == '__main__':
    asyncio.run(main())

