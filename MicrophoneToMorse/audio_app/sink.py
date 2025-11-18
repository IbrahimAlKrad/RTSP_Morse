#!/usr/bin/env python

import signal
import sys
from typing import Generic, Optional, TypeVar
from google.protobuf.message import Message
from confluent_kafka import Consumer

from .utils import WarningThrottler


InputT = TypeVar("InputT", bound=Message)


class Sink(Generic[InputT]):
    INPUT_TYPE: type[InputT] = None

    SOURCE_TOPIC: str = None
    GROUP_ID: str = None
    KAFKA_KEY: bytes = None

    KAFKA_BROKER: str = "localhost:9092"

    def __init__(
        self,
        source_topic: Optional[str] = None,
        group_id: Optional[str] = None,
        kafka_key: Optional[bytes] = None,
        kafka_broker: Optional[str] = None,
    ):
        self.source_topic = source_topic or self.SOURCE_TOPIC
        self.group_id = group_id or self.GROUP_ID
        self.kafka_key = kafka_key or self.KAFKA_KEY
        self.kafka_broker = kafka_broker or self.KAFKA_BROKER

        if not self.source_topic:
            raise ValueError("SOURCE_TOPIC must be set")
        if not self.group_id:
            raise ValueError("GROUP_ID must be set")
        if self.INPUT_TYPE is None:
            raise ValueError("INPUT_TYPE must be set")

        source_config = {
            "bootstrap.servers": self.kafka_broker,
            "group.id": self.group_id,
            "auto.offset.reset": "latest",
        }

        self.consumer = Consumer(source_config)
        self.consumer.subscribe([self.source_topic])

        self.warning_throttler = WarningThrottler(self.__class__.__name__)

        signal.signal(signal.SIGINT, self._shutdown)

        print(
            f"[{self.__class__.__name__}] Connected to Kafka broker at {self.kafka_broker}"
        )
        print(f"[{self.__class__.__name__}] Consuming from '{self.source_topic}'")

    def consume(self, input_msg: InputT):
        raise NotImplementedError("Subclasses must implement consume()")

    def on_consume_error(self, error: Exception, input_msg: InputT) -> None:
        print(f"[{self.__class__.__name__}] Error consuming message: {error}")

    def print_warning(self, key: str, message: str) -> bool:
        return self.warning_throttler.warn(key, message)

    def _shutdown(self, sig, frame):
        print(f"[{self.__class__.__name__}] Caught SIGINT - shutting down...")
        try:
            self.consumer.close()
        except Exception:
            pass
        sys.exit(0)

    def run(self):
        while True:
            msg = self.consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.key() != self.kafka_key:
                continue

            try:
                input_msg = self.INPUT_TYPE()
                input_msg.ParseFromString(msg.value())
            except Exception as e:
                print(f"[{self.__class__.__name__}] Error deserializing message: {e}")
                continue

            try:
                self.consume(input_msg)
            except Exception as e:
                self.on_consume_error(e, input_msg)
