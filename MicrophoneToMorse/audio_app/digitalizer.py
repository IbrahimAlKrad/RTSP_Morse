#!/usr/bin/env python

import signal
import sys
import numpy as np
from confluent_kafka import Consumer, Producer
import collections
import time
from .generated import morse_frame_pb2, digital_frame_pb2

TARGET_FREQUENCY = 400
KAFKA_KEY = b"400"

KAFKA_BROKER = "localhost:9092"
SOURCE_TOPIC = "frequency_intensity"
TARGET_TOPIC = "frequency_digital"
GROUP_ID = "digital-extractor-group"


def shutdown(sig, frame):
    print("[goertzel] Caught SIGINT - shutting down...")
    try:
        consumer.close()
    except Exception:
        pass
    try:
        print("Flushing remaining Kafka messages...")
        producer.flush()
        print("Done.")
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown)

    source_config = {
        "bootstrap.servers": KAFKA_BROKER,
        "group.id": GROUP_ID,
        "auto.offset.reset": "latest",
    }

    target_config = {"bootstrap.servers": KAFKA_BROKER, "acks": "all"}

    consumer = Consumer(source_config)
    consumer.subscribe([SOURCE_TOPIC])

    producer = Producer(target_config)

    print(f"Connected to Kafka broker at {KAFKA_BROKER}")

    WARNING_INTERVAL = 5.0
    last_warning_times = collections.defaultdict(lambda: 0)

    def print_warning(msg, key):
        global last_warning_times

        current_time = time.time()
        if (current_time - last_warning_times[key]) > WARNING_INTERVAL:
            print(f"Warning: {msg}")
            last_warning_times[key] = current_time

    def delivery_callback(err, msg):
        if err:
            print("ERROR: Message failed delivery: {}".format(err))

    print(f"Consuming from '{SOURCE_TOPIC}' and producing to '{TARGET_TOPIC}'...")
    while True:
        msg = consumer.poll(timeout=1.0)

        if msg is None:
            print("Waiting...")
        else:
            chunk = morse_frame_pb2.MorseFrame()
            chunk.ParseFromString(msg.value())

            #TODO:improve detection using maybe floating average for noise
            high = True if chunk.magnitude > 0.01 else False

            frame = digital_frame_pb2.DigitalFrame()
            frame.high = high
            frame.frequency = TARGET_FREQUENCY

            serialized_data = frame.SerializeToString()

            producer.produce(
                TARGET_TOPIC,
                key=KAFKA_KEY,
                value=serialized_data,
                callback=delivery_callback,
            )

            producer.poll(0)
