# Partial Pipeline (Microphone to Morsecode)

This part of the pipeline reads from a microphone, splits by transmit frequency and extracts the detected morse code in an apache Kafka pipeline.

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
```

## Running the scripts

The pipeline can be started by running

```bash
uv python -m audio_app
```

Currently, they are only example scripts that read from the microphone and write to a kafka topic, where the consumer reads it and display and animated graph of the volume to check if it is working.
