import os
import json
import asyncio
import websockets
from http.server import HTTPServer, SimpleHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor
import threading

WEBSOCKET_PORT = 8080
HTTP_PORT = 8080

connected_clients = set()

async def websocket_handler(websocket, path):
    try:
        connected_clients.add(websocket)
        print(f"Client connected. Total clients: {len(connected_clients)}")
        
        async for message in websocket:
            try:
                data = json.loads(message)
                # Handle the message based on your protocol
                response = {"status": "received", "message": data}
                await websocket.send(json.dumps(response))
            except json.JSONDecodeError:
                await websocket.send(json.dumps({"error": "Invalid JSON format"}))
    finally:
        connected_clients.remove(websocket)
        print(f"Client disconnected. Total clients: {len(connected_clients)}")

def run_websocket_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    start_server = websockets.serve(websocket_handler, "0.0.0.0", WEBSOCKET_PORT)
    print(f"Starting WebSocket server on port {WEBSOCKET_PORT}...")
    loop.run_until_complete(start_server)
    loop.run_forever()

def run_http_server():
    os.chdir(os.path.dirname(__file__) + "/static_content")
    server_address = ('0.0.0.0', HTTP_PORT)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f"Starting HTTP server on port {HTTP_PORT}...")
    httpd.serve_forever()

def run_server():
    # Start WebSocket server in a separate thread
    websocket_thread = threading.Thread(target=run_websocket_server)
    websocket_thread.daemon = True
    websocket_thread.start()

    # Run HTTP server in the main thread
    run_http_server()

if __name__ == "__main__":
    run_server()
