#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from confluent_kafka import Consumer
import collections

KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "raw_audio_topic"
GROUP_ID = "audio-visualizer-group"

FORMAT = np.int16
CHUNK = 1024
RATE = 44100
MAX_INT16 = 32767


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

    ax.set_ylim(0, MAX_INT16)
    ax.set_xlim(0, PLOT_HISTORY_LEN)
    ax.set_title("Live Audio Volume (RMS) from Kafka")
    ax.set_xlabel("Time (Chunks)")
    ax.set_ylabel("RMS Amplitude (Volume)")
    plt.tight_layout()

    def update_plot(frame):
        msg = consumer.poll(timeout=0.01)

        if msg is None:
            return (line,)
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            return (line,)

        raw_bytes = msg.value()
        audio_samples = np.frombuffer(raw_bytes, dtype=FORMAT)
        samples_float = audio_samples.astype(np.float64)
        rms = np.sqrt(np.mean(samples_float**2))
        plot_data.append(rms)
        line.set_ydata(np.array(plot_data))
        return (line,)

    ani = FuncAnimation(fig, update_plot, blit=True, interval=10, cache_frame_data=False)

    try:
        print(f"Consuming from '{KAFKA_TOPIC}' and visualizing RMS volume...")
        plt.show()
    except KeyboardInterrupt:
        print("Stopping visualizer...")
    finally:
        consumer.close()
        print("Done.")
