#!/usr/bin/env python

from .visualizer import Visualizer
from .generated import digital_frame_pb2


class DigitalizerVisualizer(Visualizer):
    INPUT_TYPE = digital_frame_pb2.DigitalFrame

    SOURCE_TOPIC = "frequency_digital"
    GROUP_ID = "digital-visualizer-group"
    KAFKA_KEY = b"400"

    YLIM = (0.0, 1.1)
    TITLE = "Live Digital Signal from Kafka"
    XLABEL = "Time (Chunks)"
    YLABEL = "Signal State"

    def extract_value(self, input_msg):
        return 1.0 if input_msg.high else 0.0


if __name__ == "__main__":
    sink = DigitalizerVisualizer()
    sink.run()
