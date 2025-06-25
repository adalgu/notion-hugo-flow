import os
import sys
import subprocess
from http.server import BaseHTTPRequestHandler
import json


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests for Notion webhook sync"""
        try:
            # Verify that NOTION_TOKEN is available
            if not os.getenv("NOTION_TOKEN"):
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps({"error": "NOTION_TOKEN not configured"}).encode()
                )
                return

            # Add the project root to Python path
            sys.path.insert(0, "/var/task")

            # Run the notion sync
            result = subprocess.run(
                ["python", "/var/task/notion_hugo_app.py", "--full-sync"],
                capture_output=True,
                text=True,
                cwd="/var/task",
            )

            if result.returncode == 0:
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {
                    "status": "success",
                    "message": "Notion sync completed successfully",
                    "output": result.stdout,
                }
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {
                    "status": "error",
                    "message": "Notion sync failed",
                    "error": result.stderr,
                    "output": result.stdout,
                }
                self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {
                "status": "error",
                "message": "Internal server error",
                "error": str(e),
            }
            self.wfile.write(json.dumps(response).encode())

    def do_GET(self):
        """Handle GET requests for health check"""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        response = {
            "status": "healthy",
            "message": "Notion-Hugo sync API is running",
            "version": "1.0.0",
        }
        self.wfile.write(json.dumps(response).encode())
