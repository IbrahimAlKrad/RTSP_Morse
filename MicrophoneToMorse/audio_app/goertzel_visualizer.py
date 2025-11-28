#!/usr/bin/env python

from .visualizer import Visualizer
from .generated import morse_frame_pb2


class GoertzelVisualizer(Visualizer):
    INPUT_TYPE = morse_frame_pb2.MorseFrame

    SOURCE_TOPIC = "frequency_intensity"
    GROUP_ID = "goertzel-visualizer-group"
    KAFKA_KEY = b"400"

    YLIM = (0.0, 1.0)
    TITLE = "Live Target Frequency Volume (400Hz) from Kafka"
    XLABEL = "Time (Chunks)"
    YLABEL = "Normalized Magnitude (Volume)"

    def extract_value(self, input_msg):
        return input_msg.magnitude


if __name__ == "__main__":
    sink = GoertzelVisualizer()
    sink.run()
