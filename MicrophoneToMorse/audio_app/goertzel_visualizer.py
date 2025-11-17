#!/usr/bin/env python

import signal
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from confluent_kafka import Consumer
import collections
import time
from .generated import morse_frame_pb2

KAFKA_KEY = b"400"

KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "frequency_intensity"
GROUP_ID = "goertzel-visualizer-group"


def shutdown(sig, frame):
    print("[visualizer] Caught SIGINT - shutting down...")
    try:
        consumer.close()
    except Exception:
        pass
    plt.close()
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown)

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

    def update_plot(frame):
        msg = consumer.poll(timeout=0.01)

        if msg is None:
            return (line,)
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            return (line,)

        if msg.key() != KAFKA_KEY:
            return (line,)

        morse_frame = morse_frame_pb2.MorseFrame()
        morse_frame.ParseFromString(msg.value())

        magnitude = morse_frame.magnitude

        plot_data.append(magnitude)
        line.set_ydata(np.array(plot_data))
        return (line,)

    ani = FuncAnimation(
        fig, update_plot, blit=True, interval=10, cache_frame_data=False
    )

    print(f"Consuming from '{KAFKA_TOPIC}' and visualizing frequency magnitude...")
    plt.show()
