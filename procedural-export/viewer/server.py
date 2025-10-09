#!/usr/bin/env python3
"""
Simple HTTP server for Valheim World Engine Procedural Export Viewer
Serves the web viewer and world data files
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

# Configuration
PORT = 8080
HOST = '0.0.0.0'

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to allow cross-origin requests
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    # Change to the viewer directory
    viewer_dir = Path(__file__).parent
    os.chdir(viewer_dir)
    
    # Copy data files to viewer directory if they don't exist
    output_dir = Path('../output')
    if output_dir.exists():
        import shutil
        for file in output_dir.glob('*.json'):
            dest = viewer_dir / file.name
            if not dest.exists():
                shutil.copy2(file, dest)
                print(f"Copied {file.name} to viewer directory")
    
    print(f"Starting Valheim World Engine Viewer server...")
    print(f"Server running at http://{HOST}:{PORT}")
    print(f"Serving files from: {viewer_dir}")
    print(f"Press Ctrl+C to stop the server")
    
    try:
        with socketserver.TCPServer((HOST, PORT), CustomHTTPRequestHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"Port {PORT} is already in use. Please try a different port or stop the existing server.")
        else:
            print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
