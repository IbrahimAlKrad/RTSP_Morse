#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from confluent_kafka import Consumer
import collections
import pyaudio
import time
from .generated import morse_frame_pb2

KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "raw_audio_topic"
GROUP_ID = "audio-visualizer-group"

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

    last_warning_time = 0.0
    WARNING_INTERVAL = 5.0

    def update_plot(frame):
        global last_warning_time

        msg = consumer.poll(timeout=0.01)

        if msg is None:
            return (line,)
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            return (line,)

        chunk = morse_frame_pb2.AudioChunk()
        chunk.ParseFromString(msg.value())

        try:
            dtype = DTYPE_FROM_FORMAT[chunk.data_format]
            max_amplitude = MAX_AMP_FROM_FORMAT[chunk.data_format]
        except KeyError:
            print(f"Error: Received chunk with unsupported format: {chunk.data_format}")
            return (line,)

        audio_samples = np.frombuffer(chunk.data, dtype=dtype)
        samples_float = audio_samples.astype(np.float64)
        rms = np.sqrt(np.mean(samples_float**2))
        normalized_rms = rms / max_amplitude

        if normalized_rms > 1.0:
            current_time = time.time()
            if (current_time - last_warning_time) > WARNING_INTERVAL:
                print(
                    f"Warning: Audio clipping detected! Normalized RMS: {normalized_rms:.2f}"
                )
                last_warning_time = current_time

        clamped_rms = np.clip(normalized_rms, 0.0, 1.0)
        plot_data.append(clamped_rms)
        line.set_ydata(np.array(plot_data))
        return (line,)

    ani = FuncAnimation(
        fig, update_plot, blit=True, interval=10, cache_frame_data=False
    )

    try:
        print(f"Consuming from '{KAFKA_TOPIC}' and visualizing RMS volume...")
        plt.show()
    except KeyboardInterrupt:
        print("Stopping visualizer...")
    finally:
        consumer.close()
        print("Done.")
