# Partial Pipeline (Microphone to Morsecode)

This part of the pipeline reads from a microphone, splits by transmit frequency and extracts the detected morse code in an apache Kafka pipeline.

## Installing requirements

This project uses `uv` to install and manage the Python venv and dependencies and can be restored using `uv sync`. If not using uv, `pyproject.toml` contains the required dependencies and can be used as a reference to install required dependencies.

### Note for Apple Silicon machines

On apple silicon, portaudio needs to be installed seperately for `pyaudio` to work, for example by running `brew install portaudio`.

## Running the scripts

The scripts can be started by running `uv run audio_consumer.py` and `uv run audio_producer.py`. Currently, they are only example scripts that read from the microphone and write to a kafka topic, where the consumer reads it and display and animated graph of the volume to check if it is working.
