#!/usr/bin/env python

import pyaudio
import time
from confluent_kafka import Producer
from .generated import morse_frame_pb2

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "raw_audio_topic"

if __name__ == "__main__":
    config = {"bootstrap.servers": KAFKA_BROKER, "acks": "all"}
    producer = Producer(config)
    print(f"Connected to Kafka broker at {KAFKA_BROKER}")

    p = pyaudio.PyAudio()
    stream = None

    def delivery_callback(err, msg):
        if err:
            print("ERROR: Message failed delivery: {}".format(err))

    def audio_callback(in_data, frame_count, time_info, status):
        chunk = morse_frame_pb2.MorseFrame()
        chunk.sample_rate = RATE
        chunk.channels = CHANNELS
        chunk.data_format = FORMAT
        chunk.data = in_data

        serialized_data = chunk.SerializeToString()

        producer.produce(KAFKA_TOPIC, value=serialized_data, callback=delivery_callback)

        producer.poll(0)

        return (in_data, pyaudio.paContinue)

    try:
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            stream_callback=audio_callback,
        )
        print(f"Recording and streaming to Kafka topic '{KAFKA_TOPIC}'...")
        print("Press Ctrl+C to stop")

        stream.start_stream()

        while stream.is_active():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopping stream...")
    finally:
        if stream:
            stream.stop_stream()
            stream.close()
        p.terminate()

        print("Flushing remaining Kafka messages...")
        producer.flush()
        print("Done.")
