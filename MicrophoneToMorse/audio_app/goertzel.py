#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from confluent_kafka import Consumer
import collections
import pyaudio
import time
import math
from .generated import morse_frame_pb2

TARGET_FREQUENCY = 550

KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "raw_audio_topic"
GROUP_ID = "goertzel-visualizer-group"

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


if __name__ == "__main__":
    config = {
        "bootstrap.servers": KAFKA_BROKER,
        "group.id": GROUP_ID,
        "auto.offset.reset": "latest",
    }

    consumer = Consumer(config)
    consumer.subscribe([KAFKA_TOPIC])

    PLOT_HISTORY_LEN = 200
    plot_data = collections.deque(maxlen=PLOT_HISTORY_LEN)
    plot_data.extend(np.zeros(PLOT_HISTORY_LEN))

    fig, ax = plt.subplots()
    (line,) = ax.plot(np.array(plot_data))

    ax.set_ylim(0, 1.0)
    ax.set_xlim(0, PLOT_HISTORY_LEN)
    ax.set_title("Live Audio Volume (RMS) from Kafka")
    ax.set_xlabel("Time (Chunks)")
    ax.set_ylabel("Normalized RMS Amplitude (Volume)")
    plt.tight_layout()

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

    def update_plot(frame):
        msg = consumer.poll(timeout=0.01)

        if msg is None:
            return (line,)
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            return (line,)

        chunk = morse_frame_pb2.MorseFrame()
        chunk.ParseFromString(msg.value())

        try:
            dtype = DTYPE_FROM_FORMAT[chunk.data_format]
            max_amplitude = MAX_AMP_FROM_FORMAT[chunk.data_format]
        except KeyError:
            print(f"Error: Received chunk with unsupported format: {chunk.data_format}")
            return (line,)

        audio_samples = np.frombuffer(chunk.data, dtype=dtype)
        samples_float = audio_samples.astype(np.float64)
        normalized_magnitude = goertzel(
            samples_float, chunk.sample_rate, TARGET_FREQUENCY, max_amplitude
        )
        clamped_rms = np.clip(normalized_magnitude, 0.0, 1.0)
        plot_data.append(clamped_rms)
        line.set_ydata(np.array(plot_data))
        return (line,)

    ani = FuncAnimation(
        fig, update_plot, blit=True, interval=10, cache_frame_data=False
    )

    try:
        print(f"Consuming from '{KAFKA_TOPIC}' and visualizing frequency magnitude...")
        plt.show()
    except KeyboardInterrupt:
        print("Stopping visualizer...")
    finally:
        consumer.close()
        print("Done.")
