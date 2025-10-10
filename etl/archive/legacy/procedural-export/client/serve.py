#!/usr/bin/env python3
"""
Simple HTTP server for Valheim map viewer
Serves client/ directory with CORS enabled
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 8080

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def log_message(self, format, *args):
        # Colorized logging
        if '200' in str(args):
            status = '\033[92m200\033[0m'  # Green
        elif '404' in str(args):
            status = '\033[91m404\033[0m'  # Red
        else:
            status = str(args[1])

        print(f"[{self.log_date_time_string()}] {args[0]} - {status}")

if __name__ == '__main__':
    # Change to procedural-export directory (parent of client/)
    os.chdir(Path(__file__).parent.parent)

    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        print("=" * 60)
        print("Valheim Map Viewer Server")
        print("=" * 60)
        print(f"Server running at: http://localhost:{PORT}/client/")
        print(f"Serving from: {os.getcwd()}")
        print("\nPress Ctrl+C to stop")
        print("=" * 60)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nShutting down server...")
            httpd.shutdown()
