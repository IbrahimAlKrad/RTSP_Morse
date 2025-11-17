#!/usr/bin/env python

import signal
import sys
from typing import Generic, Optional, TypeVar
from google.protobuf.message import Message
from confluent_kafka import Consumer, Producer

from .utils import WarningThrottler


InputT = TypeVar("InputT", bound=Message)
OutputT = TypeVar("OutputT", bound=Message)


class StreamOperator(Generic[InputT, OutputT]):
    INPUT_TYPE: type[InputT] = None
    OUTPUT_TYPE: type[OutputT] = None

    SOURCE_TOPIC: str = None
    TARGET_TOPIC: str = None
    GROUP_ID: str = None
    KAFKA_KEY: bytes = None

    KAFKA_BROKER: str = "localhost:9092"

    def __init__(
        self,
        source_topic: Optional[str] = None,
        target_topic: Optional[str] = None,
        group_id: Optional[str] = None,
        kafka_key: Optional[bytes] = None,
        kafka_broker: Optional[str] = None,
    ):
        self.source_topic = source_topic or self.SOURCE_TOPIC
        self.target_topic = target_topic or self.TARGET_TOPIC
        self.group_id = group_id or self.GROUP_ID
        self.kafka_key = kafka_key or self.KAFKA_KEY
        self.kafka_broker = kafka_broker or self.KAFKA_BROKER

        if not self.source_topic:
            raise ValueError("SOURCE_TOPIC must be set")
        if not self.target_topic:
            raise ValueError("TARGET_TOPIC must be set")
        if not self.group_id:
            raise ValueError("GROUP_ID must be set")
        if self.INPUT_TYPE is None:
            raise ValueError("INPUT_TYPE must be set")
        if self.OUTPUT_TYPE is None:
            raise ValueError("OUTPUT_TYPE must be set")

        source_config = {
            "bootstrap.servers": self.kafka_broker,
            "group.id": self.group_id,
            "auto.offset.reset": "latest",
        }
        target_config = {"bootstrap.servers": self.kafka_broker, "acks": "all"}

        self.consumer = Consumer(source_config)
        self.consumer.subscribe([self.source_topic])

        self.producer = Producer(target_config)

        self.warning_throttler = WarningThrottler(self.__class__.__name__)

        signal.signal(signal.SIGINT, self._shutdown)

        print(
            f"[{self.__class__.__name__}] Connected to Kafka broker at {self.kafka_broker}"
        )
        print(
            f"[{self.__class__.__name__}] Consuming from '{self.source_topic}' and producing to '{self.target_topic}'"
        )

    def process(self, input_msg: InputT) -> Optional[OutputT]:
        raise NotImplementedError("Subclasses must implement process()")

    def on_process_error(self, error: Exception, input_msg: InputT) -> None:
        print(f"[{self.__class__.__name__}] Error processing message: {error}")

    def print_warning(self, key: str, message: str) -> bool:
        return self.warning_throttler.warn(key, message)

    def _delivery_callback(self, err, msg):
        if err:
            print(f"[{self.__class__.__name__}] Error delivering message: {err}")

    def _shutdown(self, sig, frame):
        print(f"[{self.__class__.__name__}] Caught SIGINT - shutting down...")
        try:
            self.consumer.close()
        except Exception:
            pass
        try:
            print(f"[{self.__class__.__name__}] Flushing remaining Kafka messages...")
            self.producer.flush()
            print(f"[{self.__class__.__name__}] Done.")
        except Exception:
            pass
        sys.exit(0)

    def run(self):
        while True:
            msg = self.consumer.poll(timeout=1.0)

            if msg is None:
                continue

            try:
                input_msg = self.INPUT_TYPE()
                input_msg.ParseFromString(msg.value())
            except Exception as e:
                print(f"[{self.__class__.__name__}] Error deserializing message: {e}")
                continue

            try:
                output_msg = self.process(input_msg)
            except Exception as e:
                self.on_process_error(e, input_msg)
                continue

            if output_msg is None:
                continue

            try:
                serialized_data = output_msg.SerializeToString()
                self.producer.produce(
                    self.target_topic,
                    key=self.kafka_key,
                    value=serialized_data,
                    callback=self._delivery_callback,
                )
                self.producer.poll(0)
            except Exception as e:
                print(f"[{self.__class__.__name__}] Error producing message: {e}")
