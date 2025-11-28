# Partial Pipeline (Microphone to Morsecode)

This part of the pipeline reads from a microphone, splits by transmit frequency and extracts the detected morse code in an apache Kafka pipeline.

## Input expectations

This pipeline expects the input to be morse audio according to the following specification:

- `dit_duration` is equal to 0.1s and will be used in the calculation of durations in the following.
- A dot (.) has a duration of `dit_duration`.
- A dash (-) has a duration of `3 * dit_duration`.
- A pause between symbols is `dit_duration`.
- A pause between words is `7 * dit_duration`.
- The pipeline allows for some tolerance, but this should be the target durations.

## Installing requirements

This project uses `uv` to install and manage the Python venv and dependencies and can be restored using `uv sync`. If not using uv, `pyproject.toml` contains the required dependencies and can be used as a reference to install required dependencies.

This project uses `protobuf` to manage type safe communication between services. The compiler has to be installed in order to generate the files from a schema definition, for example by running `brew install protobuf`.

### Note for Apple Silicon machines

On apple silicon, portaudio needs to be installed seperately for `pyaudio` to work, for example by running `brew install portaudio`.

## Compiling the schemas

Before running the scripts, the protobuf schemas need to be generated from the root of the project by running

```bash
protoc -I=protos --python_out=audio_app/generated protos/audio_chunk.proto
protoc -I=protos --python_out=audio_app/generated protos/morse_frame.proto
protoc -I=protos --python_out=audio_app/generated protos/digital_frame.proto
protoc -I=protos --python_out=audio_app/generated protos/morse_symbol.proto
```

## Running the scripts

The application expects a kafka broker to be running at `localhost:9092`. The `docker-compose.yml` can be used to achieve exactly this by running

```bash
docker compose up -d
```

and be shut down after finishing the app using

```bash
docker compose down -v
```

The pipeline with debug visualizers can be started by running

```bash
uv run python -m audio_app
```

The final sink (morse code transcriber) can be viewed in a console using

```bash
uv run python -m audio_app.morser_visualizer
```

## External Documentation

This project heavily uses the Python package `confluent_kafka`. The [official documenation](https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#) provides helpful insights.
