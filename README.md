# RTSP_Morse

A collection of tools and applications for Morse code processing, including microphone-to-Morse conversion, text-to-Morse audio generation, and speech-to-text transcription.

## Project Structure

### SoundToMorse

A Python-based pipeline that reads audio from a microphone, processes it through an Apache Kafka streaming architecture, and extracts Morse code. The pipeline uses the Goertzel algorithm for frequency detection and includes visualization tools for debugging.

**Key Features:**
- Real-time audio capture and processing
- Kafka-based message streaming
- Protobuf for type-safe communication between services
- Configurable Morse code timing parameters

**Technologies:** Python, Apache Kafka, Protobuf, NumPy, PyAudio, Matplotlib

### TextToSound

A real-time system that converts text to Morse code audio. It consists of a Python backend that handles text-to-Morse conversion and a React Router v7 frontend that plays the audio.

**Architecture:**
- User Input → `text_input` topic → Python Backend → `morse_output` topic → Frontend → Audio

**Key Features:**
- Web-based user interface
- Real-time text-to-Morse conversion
- Kafka message broker for communication
- Health monitoring via heartbeat messages

**Technologies:** Python, React, Bun, Docker, Apache Kafka

### SpeechToText

A .NET 8 application for real-time audio processing and speech-to-text transcription using the Vosk speech recognition toolkit.

**Key Features:**
- Real-time microphone audio capture using NAudio
- Opus audio codec support
- Vosk-based speech-to-text transcription
- Audio resampling capabilities
- Debug console with metrics display

**Technologies:** C#, .NET 8, NAudio, Vosk, OpusSharp

**Contents:**
- `Melanocetus/`: Main application source code
- `Melanocetus.sln`: Visual Studio solution file
- `Misc/`: Configuration files and Vosk speech recognition models
  - `melanocetus.json`: Audio configuration settings (sample rates, frame duration, device selection)
  - `models/`: Pre-trained Vosk speech recognition models (e.g., `vosk-model-small-en-us-0.15`)

## Getting Started

Refer to the individual sub-project READMEs for detailed setup instructions:

- [SoundToMorse/README.md](SoundToMorse/README.md) - Python Kafka pipeline for Morse code extraction
- [TextToSound/README.md](TextToSound/README.md) - Text-to-Morse web application

For SpeechToText, open the solution file `SpeechToText/Melanocetus.sln` in Visual Studio and build the project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
