#!/usr/bin/env python3
"""Start Flask server on port 5001."""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from acs.api.app import run_server

if __name__ == '__main__':
    print("=" * 70)
    print("Starting Archaeological Classifier Server")
    print("Port: 5001")
    print("=" * 70)
    print("\nAccess the application at:")
    print("  http://localhost:5001/")
    print("\nSavignano Technical Drawings Test:")
    print("  http://localhost:5001/web/savignano-drawings-test")
    print("\n" + "=" * 70)

    run_server(host='0.0.0.0', port=5001, debug=True)
