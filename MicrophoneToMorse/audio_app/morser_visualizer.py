#!/usr/bin/env python

from .sink import Sink
from .generated import morse_symbol_pb2


class MorserVisualizer(Sink[morse_symbol_pb2.MorseSymbol]):
    INPUT_TYPE = morse_symbol_pb2.MorseSymbol

    SOURCE_TOPIC = "morse_symbols"
    GROUP_ID = "morse-visalizer-group"
    KAFKA_KEY = b"400"

    SYMBOL_TO_CHAR = {
        morse_symbol_pb2.MorseSymbol.DIT: ".",
        morse_symbol_pb2.MorseSymbol.DAH: "-",
        morse_symbol_pb2.MorseSymbol.BREAK: " ",
        morse_symbol_pb2.MorseSymbol.WORD: "/ ",
    }

    def consume(self, input_msg):
        try:
            symbol = self.SYMBOL_TO_CHAR[input_msg.symbol]
        except KeyError:
            raise Exception(f"Received unknown symbol: {input_msg.symbol}")

        print(symbol, end="", flush=True)


if __name__ == "__main__":
    sink = MorserVisualizer()
    sink.run()
