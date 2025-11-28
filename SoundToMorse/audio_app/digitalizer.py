#!/usr/bin/env python

from .operator import StreamOperator
from .generated import morse_frame_pb2, digital_frame_pb2


class DigitalizerOperator(
    StreamOperator[morse_frame_pb2.MorseFrame, digital_frame_pb2.DigitalFrame]
):
    INPUT_TYPE = morse_frame_pb2.MorseFrame
    OUTPUT_TYPE = digital_frame_pb2.DigitalFrame

    SOURCE_TOPIC = "frequency_intensity"
    TARGET_TOPIC = "frequency_digital"
    GROUP_ID = "digital-extractor-group"
    SOURCE_KAFKA_KEY = b"400"
    TARGET_KAFKA_KEY = b"400"

    TARGET_FREQUENCY = 400

    def process(
        self, input_msg: morse_frame_pb2.MorseFrame
    ) -> digital_frame_pb2.DigitalFrame:
        # TODO:improve detection using maybe floating average for noise
        high = True if input_msg.magnitude > 0.01 else False

        frame = digital_frame_pb2.DigitalFrame()
        frame.high = high
        frame.frequency = self.TARGET_FREQUENCY
        frame.timestamp = input_msg.timestamp

        return frame


if __name__ == "__main__":
    operator = DigitalizerOperator()
    operator.run()
