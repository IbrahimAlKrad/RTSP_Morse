import faust
import faust.tables
import numpy as np
import time
import pickle
import os
import asyncio

# Fix for Python 3.10+ / 3.14 where no implicit event loop exists
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

class Message (faust.Record):
    user : str
    message : str

app = faust.App('morsecode_protocoll', broker='kafka://localhost:9092', web_port=6067, topic_allow_declare=False)
sr_morse = app.topic('sr_morse', value_type = Message, key_type = str)

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

class MorseTreeNode:
   
    def __init__(self, character):
        self.data = character
        self.children = []

    def add_child(self, Node):
        self.children.append(Node)

initializer = MorseTreeNode("initialize")

# Definition of the morse tree
#### first generation ####
# childs of initializer
child_e = MorseTreeNode("e") #dot
child_t = MorseTreeNode("t") #minussign

#### second generation ####
# childs of child_e
child_i = MorseTreeNode("i") #dot dot
child_a = MorseTreeNode("a") #dot minussign

# childs of child_t
child_n = MorseTreeNode("n") #minussign dot
child_m = MorseTreeNode("m") #minussign minussign

#### third generation ####
# childs of child_i
child_s = MorseTreeNode("s") #dot dot dot
child_u = MorseTreeNode("u") #dot dot minussign

# childs of child_a
child_r = MorseTreeNode("r") #dot minussign dot
child_w = MorseTreeNode("w") #dot minussign minussign

# childs of child_n
child_d = MorseTreeNode("d") #minussign dot dot
child_k = MorseTreeNode("k") #minussign dot minussign

# childs of child_m
child_g = MorseTreeNode("g") #minussign minussign dot
child_o = MorseTreeNode("o") #minussign minussign minussign

#### fourth generation ####
# childs of child_s
child_h = MorseTreeNode("h") #dot dot dot dot
child_v = MorseTreeNode("v") #dot dot dot minussign

# childs of child_u
child_f = MorseTreeNode("f") #dot dot minussign dot

# childs of child_r
child_l = MorseTreeNode("l") #dot minussign dot dot

# childs of child_w
child_p = MorseTreeNode("p") #dot minussign minussign dot
child_j = MorseTreeNode("j") #dot minussign minussign minussign

# childs of child_d
child_b = MorseTreeNode("b") #minussign dot dot dot
child_x = MorseTreeNode("x") #minussign dot dot minussign

# childs of child_k
child_c = MorseTreeNode("c") #minussign dot minussign dot
child_y = MorseTreeNode("y") #minussign dot minussign minussign

# childs of child_g
child_z = MorseTreeNode("z") #minussign minussign dot dot
child_q = MorseTreeNode("q") #minussign minussign dot minussign
            ##################################################################################################################

#### first generation ####
# childs of initializer
initializer.add_child(child_e)
initializer.add_child(child_t)

#### second generation ####
# Connacting the tree
# connecting e's children to e
child_e.add_child(child_i)
child_e.add_child(child_a)

# connecting t's children to t
child_t.add_child(child_n)
child_t.add_child(child_m)

#### third generation ####
# child_i's children
child_i.add_child(child_s)
child_i.add_child(child_u)

# childs of child_a
child_a.add_child(child_r)
child_a.add_child(child_w)

# childs of child_n
child_n.add_child(child_d)
child_n.add_child(child_k)

# childs of child_m
child_m.add_child (child_g)
child_m.add_child (child_o)

#### fourth generation ####
# childs of child_s
child_s.add_child(child_h)
child_s.add_child(child_v)

# childs of child_u
child_u.add_child(child_f)

# childs of child_r
child_r.add_child(child_l)

# childs of child_w
child_w.add_child(child_p)
child_w.add_child(child_j)

# childs of child_d
child_d.add_child(child_b)
child_d.add_child(child_x)

# childs of child_k
child_k.add_child(child_c)
child_k.add_child(child_y)

# childs of child_g
child_g.add_child(child_z)
child_g.add_child(child_q)
            ##################################################################################################################

def translate_morse_to_text(morse_word):
    letter = morse_word.split()
    word=""
    for l in range(len(letter)):
        # Safely get character, skip if not found
        char = morse_alphabet.get(letter[l], "")
        word = word + char
    return word

def tree_translate_morse_to_text(morse_sequence):
    symbol = morse_sequence.split()
    word=""
    for l in symbol:
        characters=list(l)
        letter_class=initializer
        for i in range(len(characters)):
            if characters[i]==".":
                letter_class=letter_class.children[0]
            elif characters[i]=="-":
                letter_class=letter_class.children[1]

            if i == len(characters)-1:
                word=word+letter_class.data
    return word


@app.agent(sr_morse)
async def monitor(stream):
    async for msg in stream:

        print(msg.user + ": ")
        print(msg.message)
        word_list = msg.message.split("   ")

        sentence_translated=""
        i=0
        for word in word_list:
            if i>0:
                sentence_translated=sentence_translated+" "+translate_morse_to_text(word)
            else:
                sentence_translated=sentence_translated+translate_morse_to_text(word)
            i+=1
        print(sentence_translated)
       

if __name__ == '__main__':
    app.main ()





