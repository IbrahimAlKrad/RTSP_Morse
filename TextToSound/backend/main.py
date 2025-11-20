import sys
import json
import time
from confluent_kafka import Consumer, Producer, KafkaError, KafkaException

# Morse Code Dictionary
MORSE_CODE_DICT = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 
    'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 
    'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 
    'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 
    'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--', 
    'Z': '--..', 
    '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....', 
    '6': '-....', '7': '--...', '8': '---..', '9': '----.', '0': '-----', 
    ',': '--..--', '.': '.-.-.-', '?': '..--..', '/': '-..-.', '-': '-....-', 
    '(': '-.--.', ')': '-.--.-', ' ': ' '
}

def text_to_morse(text):
    morse_code = []
    for char in text.upper():
        if char in MORSE_CODE_DICT:
            morse_code.append(MORSE_CODE_DICT[char])
    return ' '.join(morse_code)

def main():
    # Kafka Configuration
    conf = {
        'bootstrap.servers': 'localhost:9094',
        'group.id': 'python_morse_converter',
        'auto.offset.reset': 'earliest'
    }

    producer_conf = {
        'bootstrap.servers': 'localhost:9094'
    }

    consumer = Consumer(conf)
    producer = Producer(producer_conf)

    # Topics
    input_topic = 'text_input'
    output_topic = 'morse_output'

    try:
        consumer.subscribe([input_topic])
        print(f"Listening on {input_topic}...")

        while True:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                elif msg.error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                    continue
                else:
                    print(msg.error())
                    break

            # Process message
            try:
                text_data = msg.value().decode('utf-8')
                print(f"Received: {text_data}")
                
                # Convert to Morse
                morse_result = text_to_morse(text_data)
                print(f"Converted: {morse_result}")

                # Send to Output Topic
                producer.produce(output_topic, value=morse_result.encode('utf-8'))
                producer.flush()
                print(f"Sent to {output_topic}")

            except Exception as e:
                print(f"Error processing message: {e}")

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()

if __name__ == '__main__':
    main()
