import os
import json
import asyncio
from aiohttp import web
import httpx
from anthropic.types.beta import BetaContentBlockParam, BetaMessageParam
from computer_use_demo.loop import APIProvider, PROVIDER_TO_DEFAULT_MODEL_NAME, sampling_loop
from computer_use_demo.tools import ToolResult

PORT = 8080
connected_clients = set()

class WebSocketInterface:
    def __init__(self, ws: web.WebSocketResponse):
        self.ws = ws
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.provider = APIProvider.ANTHROPIC
        self.model = PROVIDER_TO_DEFAULT_MODEL_NAME[self.provider]
        self.messages: list[BetaMessageParam] = []
        self.tools: dict[str, ToolResult] = {}
        self.responses: dict[str, tuple[httpx.Request, Any]] = {}
        self.only_n_most_recent_images = 3
        self.custom_system_prompt = ""

    async def output_callback(self, message: BetaContentBlockParam) -> None:
        """Handle output from the model."""
        if isinstance(message, dict):
            if message["type"] == "text":
                await self.ws.send_json({"response": message["text"]})
            elif message["type"] == "tool_use":
                await self.ws.send_json({
                    "tool_use": {
                        "name": message["name"],
                        "input": message["input"]
                    }
                })

    async def tool_output_callback(self, tool_output: ToolResult, tool_id: str) -> None:
        """Handle output from tools."""
        self.tools[tool_id] = tool_output
        response = {}
        if tool_output.error:
            response["error"] = tool_output.error
        if tool_output.output:
            response["output"] = tool_output.output
        if tool_output.base64_image:
            response["output_image"] = True
        if response:
            await self.ws.send_json({"function_results": response})

    async def api_response_callback(
        self,
        request: httpx.Request,
        response: Optional[Any],
        error: Optional[Exception],
    ) -> None:
        """Handle API responses."""
        if error:
            await self.ws.send_json({"error": str(error)})

    async def handle_message(self, message: str) -> None:
        """Handle incoming messages from the client."""
        if message == "!clear":
            self.messages = []
            return
            
        self.messages.append({
            "role": "user",
            "content": [{"type": "text", "text": message}],
        })

        self.messages = await sampling_loop(
            model=self.model,
            provider=self.provider,
            system_prompt_suffix=self.custom_system_prompt,
            messages=self.messages,
            output_callback=self.output_callback,
            tool_output_callback=self.tool_output_callback,
            api_response_callback=self.api_response_callback,
            api_key=self.api_key,
            only_n_most_recent_images=self.only_n_most_recent_images,
        )

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    try:
        connected_clients.add(ws)
        print(f"Client connected. Total clients: {len(connected_clients)}")
        
        interface = WebSocketInterface(ws)
        
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    if "message" in data:
                        await interface.handle_message(data["message"])
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
    app.router.add_get('/websocket', websocket_handler)  # Changed from /ws to /websocket
    app.router.add_get('/', index_handler)
    app.router.add_static('/', path=os.path.join(os.path.dirname(__file__), 'static_content'))
    
    # Add CORS middleware
    app.router.add_options('/{tail:.*}', lambda r: web.Response(headers={
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,X-Requested-With'
    }))
    
    print(f"Starting server on port {PORT}...")
    web.run_app(app, host='0.0.0.0', port=PORT)

if __name__ == "__main__":
    run_server()
