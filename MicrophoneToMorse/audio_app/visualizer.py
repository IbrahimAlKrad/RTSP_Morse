#!/usr/bin/env python

import collections
import queue
import threading
from typing import Optional
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
from audio_app.sink import Sink


class Visualizer(Sink):
    PLOT_HISTORY_LEN = 200

    YLIM: tuple[float, float] = None
    TITLE: str = None
    XLABEL: str = None
    YLABEL: str = None

    def __init__(
        self,
        source_topic: Optional[str] = None,
        group_id: Optional[str] = None,
        kafka_key: Optional[bytes] = None,
        kafka_broker: Optional[str] = None,
        ylim: Optional[str] = None,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
    ):
        super().__init__(source_topic, group_id, kafka_key, kafka_broker)

        self.ylim = ylim or self.YLIM
        self.title = title or self.TITLE
        self.xlabel = xlabel or self.XLABEL
        self.ylabel = ylabel or self.YLABEL

        if not self.ylim:
            raise ValueError("YLIM must be set")
        if not self.title:
            raise ValueError("TITLE must be set")
        if not self.xlabel:
            raise ValueError("XLABEL must be set")
        if not self.ylabel:
            raise ValueError("YLABEL must be set")

        self.data_queue = queue.Queue()

        self.plot_data = collections.deque(maxlen=self.PLOT_HISTORY_LEN)
        self.plot_data.extend(np.zeros(self.PLOT_HISTORY_LEN))

        self.fig, self.ax = plt.subplots()
        (self.line,) = self.ax.plot(np.array(self.plot_data))

        self.ax.set_ylim(*self.ylim)
        self.ax.set_xlim(0, self.PLOT_HISTORY_LEN)
        self.ax.set_title(self.title)
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)
        plt.tight_layout()

    def extract_value(self, input_msg):
        raise NotImplementedError("Subclasses must implement extract_value()")

    def consume(self, input_msg):
        next_value = self.extract_value(input_msg)
        self.data_queue.put(next_value)

    def update_plot(self, frame):
        while not self.data_queue.empty():
            try:
                value = self.data_queue.get_nowait()
                self.plot_data.append(value)
            except queue.Empty:
                break

        self.line.set_ydata(np.array(self.plot_data))
        return (self.line,)

    def _cleanup(self):
        print(f"[{self.__class__.__name__}] Closing plot...")
        plt.close()
        super()._cleanup()

    def run(self):
        consumer_thread = threading.Thread(target=super().run, daemon=True)
        consumer_thread.start()

        self.ani = FuncAnimation(
            self.fig, self.update_plot, blit=True, interval=10, cache_frame_data=False
        )

        print(f"[{self.__class__.__name__}] Showing visualization...")
        plt.show()
