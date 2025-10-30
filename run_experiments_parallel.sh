#!/bin/bash

echo "======================================"
echo "CoT vs A2A Parallel Experiments"
echo "======================================"

source venv/bin/activate

echo ""
echo "Step 1: Starting A2A server on port 8100..."
python src/a2a/server.py &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

sleep 5

echo ""
echo "Step 2: Running GSM8K experiments (parallel)..."
python src/experiments/run_gsm8k_parallel.py

echo ""
echo "Step 3: Running HotpotQA experiments (parallel)..."
python src/experiments/run_hotpotqa_parallel.py

echo ""
echo "Step 4: Shutting down server..."
kill $SERVER_PID

echo ""
echo "======================================"
echo "All experiments completed!"
echo "Results saved in ./results/"
echo "Checkpoints saved in ./checkpoints/"
echo "======================================"
