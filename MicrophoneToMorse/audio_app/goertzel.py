#!/usr/bin/env python

import signal
import sys
import numpy as np
from confluent_kafka import Consumer, Producer
import collections
import pyaudio
import time
import math
from .generated import audio_chunk_pb2, morse_frame_pb2

TARGET_FREQUENCY = 400
KAFKA_KEY = b"400"

KAFKA_BROKER = "localhost:9092"
SOURCE_TOPIC = "raw_audio_topic"
TARGET_TOPIC = "frequency_intensity"
GROUP_ID = "goertzel-extractor-group"

DTYPE_FROM_FORMAT = {
    pyaudio.paInt8: np.int8,
    pyaudio.paInt16: np.int16,
    pyaudio.paInt32: np.int32,
    pyaudio.paFloat32: np.float32,
}

MAX_AMP_FROM_FORMAT = {
    pyaudio.paInt8: np.iinfo(np.int8).max,
    pyaudio.paInt16: np.iinfo(np.int16).max,
    pyaudio.paInt32: np.iinfo(np.int32).max,
    pyaudio.paFloat32: 1.0,
}


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

    def goertzel(samples, sample_rate, target_freq, max_sample_value):
        if target_freq >= sample_rate / 2:
            print(
                f"The target frequency ({target_freq}) is too high for the sample rate ({sample_rate})"
            )
        n = len(samples)
        k = int(0.5 + ((n * target_freq) / sample_rate))
        omega = (2.0 * math.pi * k) / n
        coeff = 2.0 * math.cos(omega)

        s_prev = 0.0
        s_prev2 = 0.0

        for sample in samples:
            s = sample + coeff * s_prev - s_prev2
            s_prev2 = s_prev
            s_prev = s

        power = s_prev2**2 + s_prev**2 - coeff * s_prev * s_prev2
        magnitude = math.sqrt(power)
        max_magnitude = (max_sample_value * n) / 2
        normalized_magnitude = magnitude / max_magnitude

        if normalized_magnitude > 1.0:
            print_warning(
                f"Warning: Audio clipping detected! Normalized magnitude: {normalized_magnitude:.2f}",
                "clipping",
            )

        return normalized_magnitude

    def delivery_callback(err, msg):
        if err:
            print("ERROR: Message failed delivery: {}".format(err))

    print(f"Consuming from '{SOURCE_TOPIC}' and producing to '{TARGET_TOPIC}'...")
    while True:
        msg = consumer.poll(timeout=1.0)

        if msg is None:
            print("Waiting...")
        else:
            chunk = audio_chunk_pb2.AudioChunk()
            chunk.ParseFromString(msg.value())

            try:
                dtype = DTYPE_FROM_FORMAT[chunk.data_format]
                max_amplitude = MAX_AMP_FROM_FORMAT[chunk.data_format]
            except KeyError:
                print(
                    f"Error: Received chunk with unsupported format: {chunk.data_format}"
                )
                continue

            audio_samples = np.frombuffer(chunk.data, dtype=dtype)
            samples_float = audio_samples.astype(np.float64)
            normalized_magnitude = goertzel(
                samples_float, chunk.sample_rate, TARGET_FREQUENCY, max_amplitude
            )
            clamped_magnitude = np.clip(normalized_magnitude, 0.0, 1.0)

            frame = morse_frame_pb2.MorseFrame()
            frame.magnitude = clamped_magnitude
            frame.frequency = TARGET_FREQUENCY

            serialized_data = frame.SerializeToString()

            producer.produce(
                TARGET_TOPIC,
                key=KAFKA_KEY,
                value=serialized_data,
                callback=delivery_callback,
            )

            producer.poll(0)
