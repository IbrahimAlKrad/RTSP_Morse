import faust
import faust.tables
import numpy as np
import time
import pickle
import os
import asyncio
import morse_symbol_pb2

# Fix for Python 3.10+ / 3.14 where no implicit event loop exists
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

app = faust.App('morsecode_protocoll', broker='kafka://localhost:9092', web_port=6067, topic_allow_declare=False)
# Consume raw bytes from the morse_symbols topic
morse_topic = app.topic('morse_symbols', value_type=bytes, value_serializer='raw')

morse_alphabet = {".-":"a",
                 "-...":"b",
                 "-.-.":"c",
                 "-..":"d",
                 ".":"e",
                 "..-.":"f",
                 "--.":"g",
                 "....":"h",
                 "..":"i",
                 ".---":"j",
                 "-.-":"k",
                 ".-..":"l",
                 "--":"m",
                 "-.":"n",
                 "---":"o",
                 ".--.":"p",
                 "--.-":"q",
                 ".-.":"r",
                 "...":"s",
                 "-":"t",
                 "..-":"u",
                 "...-":"v",
                 ".--":"w",
                 "-..-":"x",
                 "-.--":"y",
                 "--..":"z",
                 ".-.-":"ä",
                 "---.":"ö",
                 "..--":"ü",
                 "...--..":"ß"}

def translate_morse_to_text(morse_word):
    return morse_alphabet.get(morse_word, "")

class MorseDecoder:
    def __init__(self):
        self.current_symbol_sequence = ""

    def process_symbol(self, sym) -> str:
        output = ""
        if sym == morse_symbol_pb2.MorseSymbol.Symbol.DIT:
            self.current_symbol_sequence += "."
        elif sym == morse_symbol_pb2.MorseSymbol.Symbol.DAH:
            self.current_symbol_sequence += "-"
        elif sym == morse_symbol_pb2.MorseSymbol.Symbol.BREAK:
            if self.current_symbol_sequence:
                letter = translate_morse_to_text(self.current_symbol_sequence)
                if letter:
                    output = letter
                self.current_symbol_sequence = ""
        elif sym == morse_symbol_pb2.MorseSymbol.Symbol.WORD:
            if self.current_symbol_sequence:
                letter = translate_morse_to_text(self.current_symbol_sequence)
                if letter:
                    output += letter
                self.current_symbol_sequence = ""
            output += " "
        return output

@app.agent(morse_topic)
async def monitor(stream):
    decoder = MorseDecoder()
    async for msg_bytes in stream:
        try:
            input_symbol = morse_symbol_pb2.MorseSymbol()
            input_symbol.ParseFromString(msg_bytes)
            
            text_fragment = decoder.process_symbol(input_symbol.symbol)
            if text_fragment:
                print(text_fragment, end="", flush=True)
                
        except Exception as e:
            print(f"Error processing message: {e}")

if __name__ == '__main__':
    app.main()





