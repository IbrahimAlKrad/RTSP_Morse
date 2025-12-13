import threading
import json
import os
import logging
from dotenv import load_dotenv
from confluent_kafka import Consumer, Producer, KafkaError
from constants import MORSE_CODE_DICT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9095")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "python_morse_converter")
TEXT_TOPIC = os.getenv("TEXT_TOPIC", "text_input")
SPEECH_TOPIC = os.getenv("SPEECH_TOPIC", "TEXT")
OUTPUT_TOPIC = os.getenv("OUTPUT_TOPIC", "morse_output")
HEARTBEAT_TOPIC = os.getenv("HEARTBEAT_TOPIC", "backend_health")


def text_to_morse(text: str) -> str:
    """Convert text to Morse code."""
    morse_code = []
    for char in text.upper():
        if char in MORSE_CODE_DICT:
            morse_code.append(MORSE_CODE_DICT[char])
    return " ".join(morse_code)


def heartbeat_publisher(
    producer: Producer, heartbeat_topic: str, stop_event: threading.Event
) -> None:
    """Publishes heartbeat messages to indicate backend is alive"""
    while not stop_event.is_set():
        try:
            # Send simple heartbeat
            heartbeat_data = {"status": "alive"}
            heartbeat_msg = json.dumps(heartbeat_data)
            producer.produce(heartbeat_topic, value=heartbeat_msg.encode("utf-8"))
            producer.flush()
            logger.info("[Heartbeat] Published")
        except Exception as e:
            logger.error(f"[Heartbeat] Error: {e}")

        # Wait 3 seconds before next heartbeat
        stop_event.wait(3)


def main() -> None:
    # Kafka Configuration
    conf = {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": KAFKA_GROUP_ID,
        "auto.offset.reset": "earliest",
    }

    producer_conf = {"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS}

    consumer = Consumer(conf)
    producer = Producer(producer_conf)

    # Start heartbeat thread
    stop_event = threading.Event()
    heartbeat_thread = threading.Thread(
        target=heartbeat_publisher,
        args=(producer, HEARTBEAT_TOPIC, stop_event),
        daemon=True,
    )
    heartbeat_thread.start()
    logger.info(f"[Heartbeat] Started publishing to {HEARTBEAT_TOPIC}")

    try:
        consumer.subscribe([TEXT_TOPIC, SPEECH_TOPIC])
        logger.info(f"Listening on {TEXT_TOPIC} and {SPEECH_TOPIC}...")

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
                    logger.error(msg.error())
                    break

            # Process message
            try:
                # Handle different topics and formats
                topic = msg.topic()
                text_data = ""
                source = "text"

                if topic == SPEECH_TOPIC:
                    # Expecting Faust JSON format: {"user": "...", "message": "..."}
                    try:
                        json_data = json.loads(msg.value().decode("utf-8"))
                        text_data = json_data.get("message", "")
                        source = "speech"
                        logger.info(f"Received speech input: {text_data}")
                    except json.JSONDecodeError:
                        # Fallback: Treat as raw string (used by Melanocetus)
                        text_data = msg.value().decode("utf-8")
                        source = "speech"
                        logger.info(f"Received raw speech input: {text_data}")
                else:
                    # Default/Text topic - Expecting raw string
                    text_data = msg.value().decode("utf-8")
                    source = "text"
                    logger.info(f"Received text input: {text_data}")

                if not text_data:
                    continue

                # Convert to Morse
                morse_result = text_to_morse(text_data)

                # Prepare output payload
                output_payload = {
                    "source": source,
                    "morse": morse_result,
                    "original_text": text_data,
                }

                # Send to Output Topic as JSON
                producer.produce(
                    OUTPUT_TOPIC, value=json.dumps(output_payload).encode("utf-8")
                )
                producer.flush()
                logger.info(f"Sent to {OUTPUT_TOPIC}: {output_payload}")

            except Exception as e:
                logger.error(f"Error processing message: {e}")

    except KeyboardInterrupt:
        logger.info("\n[Shutdown] Stopping heartbeat...")
        stop_event.set()
        heartbeat_thread.join(timeout=1)
    finally:
        consumer.close()
        logger.info("[Shutdown] Consumer closed")


if __name__ == "__main__":
    main()
