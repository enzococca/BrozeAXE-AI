#!/bin/bash
set -e

echo "========================================="
echo "Installing missing dependencies..."
echo "========================================="

# Install critical packages that Railway cache is ignoring
python3 -m pip install --no-cache-dir anthropic>=0.40.0 dropbox>=11.36.0 reportlab>=4.0.0

echo "========================================="
echo "Dependency installation complete!"
echo "========================================="

# Start the Flask application
cd archaeological-classifier
python3 -m acs.api.app
