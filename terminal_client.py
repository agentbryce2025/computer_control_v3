#!/usr/bin/env python3
import sys
import json
import requests
from websocket import create_connection
import threading
import queue
import signal
import time

# Configuration
DOCKER_WS_URL = "ws://localhost:8080/websocket"
DOCKER_HTTP_URL = "http://localhost:8080"

def check_server_ready():
    """Check if the computer-control server is running and ready"""
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            response = requests.get(DOCKER_HTTP_URL)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            if attempt < max_attempts - 1:
                print(f"Server not ready, retrying in 2 seconds... (attempt {attempt + 1}/{max_attempts})")
                time.sleep(2)
            continue
    return False

class TerminalClient:
    def __init__(self):
        self.ws = None
        self.message_queue = queue.Queue()
        self.running = True
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        print("\nShutting down...")
        self.running = False
        if self.ws:
            self.ws.close()
        sys.exit(0)

    def connect(self):
        try:
            # Add necessary headers for Streamlit WebSocket connection
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Sec-WebSocket-Version": "13",
                "Origin": "http://localhost:8080",
                "Pragma": "no-cache",
                "Cache-Control": "no-cache"
            }
            
            self.ws = create_connection(DOCKER_WS_URL, header=headers)
            print("Connected to computer-control server")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False

    def receive_messages(self):
        while self.running:
            try:
                message = self.ws.recv()
                response = json.loads(message)
                if "error" in response:
                    print(f"\nError: {response['error']}")
                elif "response" in response:
                    print(f"\nAssistant: {response['response']}")
                elif "tool_use" in response:
                    tool = response["tool_use"]
                    print(f"\nTool Use: {tool['name']}")
                    print(f"Input: {tool['input']}")
                elif "function_results" in response:
                    results = response["function_results"]
                    if "error" in results:
                        print(f"\nTool Error: {results['error']}")
                    if "output" in results:
                        print(f"\nTool Output: {results['output']}")
                    if "output_image" in results:
                        print("\nScreenshot taken")
            except Exception as e:
                if self.running:
                    print(f"\nError receiving message: {e}")
                break

    def send_message(self, message):
        try:
            self.ws.send(json.dumps({"message": message}))
        except Exception as e:
            print(f"Error sending message: {e}")

    def run(self):
        if not self.connect():
            return

        # Start message receiving thread
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()

        print("\nComputer Control Terminal Interface")
        print("---------------------------------------")
        print("You can:")
        print("1. Type natural language commands for Claude")
        print("   Example: 'Open Firefox and go to google.com'")
        print("2. Press Ctrl+C to quit")
        print("3. Type 'clear' to clear the conversation")
        print("---------------------------------------")

        try:
            while self.running:
                message = input("\nYou: ").strip()
                
                if message.lower() == 'clear':
                    # Send a special message to clear the conversation
                    self.send_message("!clear")
                    print("\nConversation cleared.")
                    continue
                elif message:
                    self.send_message(message)
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            if self.ws:
                self.ws.close()

def main():
    # Check if server is ready before starting the client
    if not check_server_ready():
        print("Error: Computer-control server is not running or not accessible.")
        print("Make sure to run 'docker-compose up computer-control' first.")
        sys.exit(1)
        
    client = TerminalClient()
    client.run()

if __name__ == "__main__":
    main()