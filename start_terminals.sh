#!/bin/bash

# Start the frontend in a new terminal window
gnome-terminal -- bash -c "echo 'Starting Frontend...'; cd fpredict_web && yarn dev; exec bash"

# Start the backend in a separate terminal window
gnome-terminal -- bash -c "echo 'Starting Backend...'; uvicorn src.api.main:app --reload; exec bash"
