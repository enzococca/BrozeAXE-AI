#!/usr/bin/env python3
"""
Start Archaeological Classifier System Web Interface
====================================================

Quick launcher for the web interface.
"""

from acs.api.app import create_app

if __name__ == '__main__':
    print("=" * 80)
    print("Archaeological Classifier System - Web Interface")
    print("=" * 80)
    print()
    print("Starting web server...")
    print("Access the interface at: http://localhost:5001/web/")
    print("API documentation at: http://localhost:5001/api/docs")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 80)
    print()

    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=True)
