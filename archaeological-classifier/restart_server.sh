#!/bin/bash
# Restart Server Script - Archaeological Classifier
# Porta 5001

echo "========================================================================"
echo "Archaeological Classifier - Server Restart"
echo "========================================================================"

# Step 1: Kill any existing servers on port 5001
echo ""
echo "[1/3] Checking for existing servers on port 5001..."
PIDS=$(lsof -ti:5001)
if [ -n "$PIDS" ]; then
    echo "      Found servers: $PIDS"
    echo "      Killing processes..."
    kill -9 $PIDS 2>/dev/null
    sleep 2
    echo "      ✓ Old servers stopped"
else
    echo "      ✓ Port 5001 is free"
fi

# Step 2: Verify port is free
echo ""
echo "[2/3] Verifying port 5001 is available..."
if lsof -i:5001 >/dev/null 2>&1; then
    echo "      ✗ ERROR: Port 5001 still in use!"
    echo "      Please manually check: lsof -i:5001"
    exit 1
else
    echo "      ✓ Port 5001 is ready"
fi

# Step 3: Start the server
echo ""
echo "[3/3] Starting Archaeological Classifier Server..."
echo "      Metadata fix applied: JSON parsing for technical drawings"
echo ""
python3 start_server_5001.py

