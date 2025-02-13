import os
import json
import asyncio
from aiohttp import web

PORT = 8080
connected_clients = set()

async def handle_computer_action(data):
    """Handle computer control actions"""
    try:
        if "action" not in data:
            return {"error": "Missing 'action' field in request"}
            
        action = data["action"]
        # Here you would implement the actual computer control logic
        # For now, we'll just echo back the request
        return {"status": "success", "function_results": data}
    except Exception as e:
        return {"error": str(e)}

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    try:
        connected_clients.add(ws)
        print(f"Client connected. Total clients: {len(connected_clients)}")
        
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    if "message" in data:
                        response = await handle_computer_action(data["message"])
                        await ws.send_json(response)
                    else:
                        await ws.send_json({"error": "Missing 'message' field in request"})
                except json.JSONDecodeError:
                    await ws.send_json({"error": "Invalid JSON format"})
            elif msg.type == web.WSMsgType.ERROR:
                print(f'WebSocket connection closed with exception {ws.exception()}')
    finally:
        connected_clients.remove(ws)
        print(f"Client disconnected. Total clients: {len(connected_clients)}")
        
    return ws

async def index_handler(request):
    return web.FileResponse(os.path.join(os.path.dirname(__file__), 'static_content', 'index.html'))

def run_server():
    app = web.Application()
    app.router.add_get('/ws', websocket_handler)
    app.router.add_get('/', index_handler)
    app.router.add_static('/', path=os.path.join(os.path.dirname(__file__), 'static_content'))
    
    print(f"Starting server on port {PORT}...")
    web.run_app(app, host='0.0.0.0', port=PORT)

if __name__ == "__main__":
    run_server()
