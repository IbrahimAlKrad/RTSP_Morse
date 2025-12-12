import faust
import asyncio
import faust.tables
import numpy as np
import speech_recognition as sr
import time
import pickle
import os

# Fix for Python 3.10+ / 3.14 where no implicit event loop exists
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())


r=sr.Recognizer()
mic=sr.Microphone()

morse_alphabet_inverse = {"a":".-",
                 "b":"-...",
                 "c":"-.-.",
                 "d":"-..",
                 "e":".",
                 "f":"..-.",
                 "g":"--.",
                 "h":"....",
                 "i":"..",
                 "j":".---",
                 "k":"-.-",
                 "l":".-..",
                 "m":"--",
                 "n":"-.",
                 "o":"---",
                 "p":".--.",
                 "q":"--.-",
                 "r":".-.",
                 "s":"...",
                 "t":"-",
                 "u":"..-",
                 "v":"...-",
                 "w":".--",
                 "x":"-..-",
                 "y":"-.--",
                 "z":"--.."}


def translate_single_word_to_morse(word):
    letter = list(word)
    symbols=""
    for l in range(len(letter)):
        # Safely get morse code, skip if not found
        code = morse_alphabet_inverse.get(letter[l], "")
        if code:
            symbols = symbols + " " + code
    return symbols

class Message (faust.Record):
    user : str
    message : str

def speech_to_str():
    with mic as source:
            audio = r.listen(source)

    try:
        return r.recognize_google(audio, language = r"de-DE")
    except sr.UnknownValueError:
        print("Keine Sprache erkannt. Bitte erneut sprechen.")
        return ""  # leere Nachricht zur�ckgeben
    except sr.RequestError as e:
        print(f"Fehler bei der Verbindung zu Google Speech API: {e}")
        return ""

app = faust.App('morsecode_sender', broker='kafka://localhost:9092', web_port=6068, topic_allow_declare=False)
sr_morse = app.topic('sr_morse', value_type = Message, key_type = str)

async def async_input():
    return await asyncio.to_thread(speech_to_str)


@app.task()
async def example_sender():
    print("Select your username: ")
    username = input()
    print("You hereby entered the chatroom.")
    while True:
  
        message = await async_input()
        print(message)
        word_list = message.lower().split()

        sentence_translated=""
        i=0
        for word in word_list:
            if i>0:
                sentence_translated=sentence_translated+"   "+translate_single_word_to_morse(word)
            else:
                sentence_translated=sentence_translated+translate_single_word_to_morse(word)
            i+=1

        await sr_morse.send(
            value = Message(user = username, message = sentence_translated), key = "reading" 
        )


       

if __name__ == '__main__':
    app.main ()




