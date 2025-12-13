# TextToSound

A real-time system that converts text to Morse code audio using a Python backend and React Router v7 frontend, communicating via Kafka message broker.

## Architecture

**Flow:** User Input → `text_input` topic → Python Backend → `morse_output` topic → Frontend → Audio

**Kafka Topics:**
- `text_input`: Frontend → Backend (plain text)
- `morse_output`: Backend → Frontend (morse code)

Both topics are auto-created by Kafka on first use.

## Prerequisites

- Docker & Docker Compose
- Bun (for frontend)
- Python 3.12+ & uv (for backend)

## Configuration

 Both backend and frontend use environment variables for configuration.

 ### Backend

 **Default `.env` content:**
 ```ini
 KAFKA_BOOTSTRAP_SERVERS=45.88.110.47:9095
 KAFKA_GROUP_ID=python_morse_converter
 TEXT_TOPIC=text_input
 SPEECH_TOPIC=STT-Text
 OUTPUT_TOPIC=morse_output
 HEARTBEAT_TOPIC=backend_health
 ```

 ### Frontend

 **Default `.env` content:**
 ```ini
 KAFKA_BROKERS=45.88.110.47:9095
 ```

## SpeechToText Integration
The system is integrated with the `Melanocetus` SpeechToText service running on the Remote Server.
1. `Melanocetus` sends recognized text to Kafka topic `STT-Text`.
2. `TextToSound` backend listens to `STT-Text` topic.
3. Users can enable "Speech Input" in the frontend to visualize this flow.

## Setup & Run

### 1. Kafka Infrastructure
Kafka is running on the **Remote Server** (`45.88.110.47:9095`). You DO NOT need to run `docker-compose up` locally.

### Alternative: Running Locally (Docker)
If you prefer to run everything locally:
1. Start local Kafka:
   ```bash
   cd TextToSound
   docker-compose up -d
   ```
2. Update `.env` files in `backend/` and `frontend/` to use `localhost:9095`:
   ```ini
   KAFKA_BOOTSTRAP_SERVERS=localhost:9095
   KAFKA_BROKERS=localhost:9095
   ```

### 2. Start Python Backend

Open a terminal in `TextToSound/backend`:

```bash
cd TextToSound/backend
uv run main.py
```

You should see:
```
Listening on text_input...
```

### 3. Start React Frontend

Open a terminal in `TextToSound/frontend`:

```bash
cd TextToSound/frontend
bun install
bun dev
```

The frontend will be available at `http://localhost:5173`.


