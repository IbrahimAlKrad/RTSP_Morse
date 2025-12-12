#!/usr/bin/env python3
"""
Simple script to publish messages to Kafka topics
Usage: python publish.py <topic> <message>
Example: python publish.py morse_output "Hello World"
"""

import sys
from confluent_kafka import Producer

def publish_message(topic: str, message: str):
    """Publish a message to a Kafka topic"""
    producer = Producer({'bootstrap.servers': 'localhost:9092'})
    
    try:
        producer.produce(topic, value=message.encode('utf-8'))
        producer.flush()
        print(f"✅ Published to {topic}: {message}")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python publish.py <topic> <message>")
        print("Example: python publish.py morse_output 'Hello iPhone'")
        sys.exit(1)
    
    topic = sys.argv[1]
    message = sys.argv[2]
    publish_message(topic, message)

