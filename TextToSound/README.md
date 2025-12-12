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
 KAFKA_BOOTSTRAP_SERVERS=localhost:9094
 KAFKA_GROUP_ID=python_morse_converter
 INPUT_TOPIC=text_input
 OUTPUT_TOPIC=morse_output
 HEARTBEAT_TOPIC=backend_health
 ```

 ### Frontend

 **Default `.env` content:**
 ```ini
 KAFKA_BROKERS=localhost:9094
 ```

## Setup & Run

### 1. Start Kafka Infrastructure

Open a terminal in `TextToSound`:

```bash
cd TextToSound
docker-compose up -d
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


