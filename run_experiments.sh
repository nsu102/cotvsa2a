#!/bin/bash

echo "======================================"
echo "CoT vs A2A Experiments Runner"
echo "======================================"

if [ ! -d "venv" ]; then
    echo "Error: venv not found. Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

source venv/bin/activate

echo ""
echo "Starting A2A server on port 8100..."
python src/a2a/server.py &
SERVER_PID=$!

sleep 3

echo ""
echo "Checking server health..."
curl -s http://localhost:8100/health

echo ""
echo ""
echo "======================================"
echo "Running GSM8K Experiments"
echo "======================================"
python src/experiments/run_gsm8k.py

echo ""
echo ""
echo "======================================"
echo "Running HotpotQA Experiments"
echo "======================================"
python src/experiments/run_hotpotqa.py

echo ""
echo "Stopping A2A server..."
kill $SERVER_PID

echo ""
echo "======================================"
echo "All experiments completed!"
echo "Check results/ directory for outputs"
echo "======================================"
