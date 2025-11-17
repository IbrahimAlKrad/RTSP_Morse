import os
import platform
import signal
import subprocess
import sys
import time
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import KafkaException, KafkaError


KAFKA_BROKER = "localhost:9092"
KAFKA_TOPICS = ["raw_audio_topic", "frequency_intensity"]


processes = []


def start(name, cmd):
    print(f"[orchestrator] Starting {name}: {cmd}")

    if platform.system() == "Windows":
        p = subprocess.Popen(
            cmd, shell=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        p = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid)
    p.name = name
    processes.append(p)
    return p


def send_sigint(proc):
    if proc.poll() is not None:
        return
    print(f"[orchestrator] Sending SIGINT to {proc.name}")
    if platform.system() == "Windows":
        proc.send_signal(signal.CTRL_BREAK_EVENT)
    else:
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)


def wait_exit(proc):
    print(f"[orchestrator] Waiting for {proc.name} to exit...")
    proc.wait()
    print(f"[orchestrator] {proc.name} exited.\n")


def shutdown(sig=None, frame=None):
    print(f"\n[orchestrator] Caught SIGINT - shutting down in reverse order...\n")
    while processes:
        proc = processes.pop()
        send_sigint(proc)
        wait_exit(proc)
    print("[orchestrator] All processes stopped. Goodbye.")
    sys.exit(0)


def create_kafka_topics_if_not_exist(bootstrap_servers, topics):
    admin = AdminClient({"bootstrap.servers": bootstrap_servers})

    futures = admin.create_topics(topics, request_timeout=15)

    for topic, future in futures.items():
        try:
            future.result()
            print(f"[orchestrator] Topic {topic} created.")
        except KafkaException as e:
            err = e.args[0]
            if err.code == KafkaError.TOPIC_ALREADY_EXISTS:
                pass
        except Exception as e:
            print(f"[orchestrator] Topic {topic} creation failed: {e}")


signal.signal(signal.SIGINT, shutdown)


def main():
    create_kafka_topics_if_not_exist(
        KAFKA_BROKER,
        [
            NewTopic(name, num_partitions=1, replication_factor=1)
            for name in KAFKA_TOPICS
        ],
    )

    start("goertzel_visualizer", "python -m audio_app.goertzel_visualizer")
    time.sleep(0.5)

    start("goertzel", "python -m audio_app.goertzel")
    time.sleep(0.5)

    start("producer", "python -m audio_app.producer")
    time.sleep(0.5)

    print("[orchestrator] Services started. Press Ctrl-C to shut down.")

    signal.pause() if platform.system() != "Windows" else time.sleep(10**9)
