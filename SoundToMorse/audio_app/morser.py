#!/usr/bin/env python

from typing import Optional
from .operator import StreamOperator
from .generated import digital_frame_pb2, morse_symbol_pb2


class MorseOperator(
    StreamOperator[digital_frame_pb2.DigitalFrame, morse_symbol_pb2.MorseSymbol]
):
    INPUT_TYPE = digital_frame_pb2.DigitalFrame
    OUTPUT_TYPE = morse_symbol_pb2.MorseSymbol

    SOURCE_TOPIC = "frequency_digital"
    TARGET_TOPIC = "morse_symbols"
    GROUP_ID = "morse-extractor-group"
    SOURCE_KAFKA_KEY = b"400"
    TARGET_KAFKA_KEY = b"400"

    TARGET_FREQUENCY = 400
    DIT_DURATION = 0.1

    def __init__(
        self,
        source_topic: Optional[str] = None,
        target_topic: Optional[str] = None,
        group_id: Optional[str] = None,
        source_kafka_key: Optional[bytes] = None,
        target_kafka_key: Optional[bytes] = None,
        kafka_broker: Optional[str] = None,
        target_frequency: Optional[int] = None,
        dit_duration: Optional[float] = None,
    ):
        super().__init__(
            source_topic,
            target_topic,
            group_id,
            source_kafka_key,
            target_kafka_key,
            kafka_broker,
        )
        self.target_frequency = target_frequency or self.TARGET_FREQUENCY
        self.dit_duration = dit_duration or self.DIT_DURATION

        self.state = "initial"
        self.t = 0
        self.err_count = 0
        self.p = 0.4  # TODO:make param
        self.last_offset = None

    def __send_symbol(self, input_msg, symbol):
        morse_symbol = morse_symbol_pb2.MorseSymbol()
        morse_symbol.symbol = symbol
        morse_symbol.frequency = input_msg.frequency
        morse_symbol.timestamp = input_msg.timestamp
        return morse_symbol

    def __error_and_reset(self, input_msg):
        self.err_count += 1
        print(
            f"[{self.__class__.__name__}] Error: Invalid state (state: {self.state}, signal: {'high' if input_msg.high else 'low'}, t: {self.t:.4f}, t_dit: {self.t / self.dit_duration:.2f}). Error count: {self.err_count}"
        )

        self.state = "initial"

        return self.__send_symbol(input_msg, morse_symbol_pb2.MorseSymbol.Symbol.BREAK)

    def process(
        self, input_msg: digital_frame_pb2.DigitalFrame
    ) -> morse_symbol_pb2.MorseSymbol:
        if self.last_offset == None:
            self.last_offset = input_msg.timestamp
        self.t = input_msg.timestamp - self.last_offset

        high = input_msg.high
        low = not high

        if self.state == "initial":
            if high:
                self.t = 0
                self.last_offset = input_msg.timestamp
                self.state = "high"
                return
            else:
                return

        elif self.state == "high":
            if high and self.t <= (1 + self.p) * self.dit_duration:
                return
            elif high and self.t > (1 + self.p) * self.dit_duration:
                self.state = "long high"
                return
            elif low and (
                (1 - self.p) * self.dit_duration
                < self.t
                <= (1 + self.p) * self.dit_duration
            ):
                self.state = "low"
                self.t = 0
                self.last_offset = input_msg.timestamp

                return self.__send_symbol(
                    input_msg, morse_symbol_pb2.MorseSymbol.Symbol.DIT
                )
            else:
                return self.__error_and_reset(input_msg)

        elif self.state == "long high":
            if high and self.t <= (1 + self.p) * 3 * self.dit_duration:
                return
            elif low and (
                (1 - self.p) * 3 * self.dit_duration
                < self.t
                <= (1 + self.p) * 3 * self.dit_duration
            ):
                self.state = "low"
                self.t = 0
                self.last_offset = input_msg.timestamp

                return self.__send_symbol(
                    input_msg, morse_symbol_pb2.MorseSymbol.Symbol.DAH
                )
            else:
                return self.__error_and_reset(input_msg)

        elif self.state == "low":
            if low and self.t <= (1 + self.p) * self.dit_duration:
                return
            elif low and self.t > (1 + self.p) * self.dit_duration:
                self.state = "long low"
                return
            elif high and (
                (1 - self.p) * self.dit_duration
                < self.t
                <= (1 + self.p) * self.dit_duration
            ):
                self.state = "high"
                self.t = 0
                self.last_offset = input_msg.timestamp
                return
            else:
                return self.__error_and_reset(input_msg)

        elif self.state == "long low":
            if low and self.t <= (1 - self.p) * 3 * self.dit_duration:
                return
            elif low and self.t > (1 - self.p) * 3 * self.dit_duration:
                self.state = "longer low"

                return self.__send_symbol(
                    input_msg, morse_symbol_pb2.MorseSymbol.Symbol.BREAK
                )
            else:
                return self.__error_and_reset(input_msg)

        elif self.state == "longer low":
            if low and self.t <= (1 - self.p) * 7 * self.dit_duration:
                return
            elif low and self.t > (1 - self.p) * 7 * self.dit_duration:
                self.state = "initial"

                return self.__send_symbol(
                    input_msg, morse_symbol_pb2.MorseSymbol.Symbol.WORD
                )
            elif high:
                self.t = 0
                self.last_offset = input_msg.timestamp
                self.state = "high"
                return
            else:
                return self.__error_and_reset(input_msg)


if __name__ == "__main__":
    operator = MorseOperator()
    operator.run()
