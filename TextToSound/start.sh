#!/bin/bash

# Ensure we are in the directory of the script
cd "$(dirname "$0")"

SESSION="text_to_sound"

# Check if session exists
tmux has-session -t $SESSION 2>/dev/null

if [ $? != 0 ]; then
  # Create new session with the first pane (Pane 0)
  tmux new-session -d -s $SESSION -n 'Dev'
  
  # Pane 0: Kafka (Docker Compose)
  tmux send-keys -t $SESSION:0.0 'docker-compose up' C-m
  
  # Split window horizontally to create Pane 1
  tmux split-window -h -t $SESSION:0
  
  # Pane 1: Backend
  tmux send-keys -t $SESSION:0.1 'cd backend && uv run main.py' C-m
  
  # Split Pane 1 vertically to create Pane 2
  tmux split-window -v -t $SESSION:0.1
  
  # Pane 2: Frontend
  tmux send-keys -t $SESSION:0.2 'cd frontend && bun dev' C-m
  
  # Select the first pane
  tmux select-pane -t $SESSION:0.0
fi

# Attach to the session
tmux attach-session -t $SESSION
