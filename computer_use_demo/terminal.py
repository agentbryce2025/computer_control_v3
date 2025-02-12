#!/usr/bin/env python3
"""
Terminal-based interface for the computer use demo.
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Any, Optional, cast

import httpx
from anthropic.types.beta import BetaContentBlockParam, BetaMessageParam

from computer_use_demo.loop import (
    APIProvider,
    PROVIDER_TO_DEFAULT_MODEL_NAME,
    sampling_loop,
)
from computer_use_demo.tools import ToolResult

class TerminalInterface:
    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "anthropic",
        model: Optional[str] = None,
        hide_images: bool = False,
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.provider = cast(APIProvider, provider)
        self.model = model or PROVIDER_TO_DEFAULT_MODEL_NAME[self.provider]
        self.hide_images = hide_images
        self.messages: list[BetaMessageParam] = []
        self.tools: dict[str, ToolResult] = {}
        self.responses: dict[str, tuple[httpx.Request, Any]] = {}
        self.only_n_most_recent_images = 3
        self.custom_system_prompt = ""

    def output_callback(self, message: BetaContentBlockParam) -> None:
        """Handle output from the model."""
        if isinstance(message, dict):
            if message["type"] == "text":
                print("\nAssistant:", message["text"])
            elif message["type"] == "tool_use":
                print(f'\nTool Use: {message["name"]}\nInput: {message["input"]}')

    def tool_output_callback(self, tool_output: ToolResult, tool_id: str) -> None:
        """Handle output from tools."""
        self.tools[tool_id] = tool_output
        if tool_output.error:
            print(f"\nTool Error: {tool_output.error}")
        if tool_output.output:
            print(f"\nTool Output: {tool_output.output}")
        if tool_output.base64_image and not self.hide_images:
            print("\nScreenshot taken (not displayed in terminal mode)")

    def api_response_callback(
        self,
        request: httpx.Request,
        response: Optional[Any],
        error: Optional[Exception],
    ) -> None:
        """Handle API responses."""
        if error:
            print(f"\nAPI Error: {error}")

    async def run(self):
        """Run the terminal interface."""
        print("Computer Control Terminal Interface")
        print("Type 'exit' or press Ctrl+C to quit")
        print("Type 'clear' to clear the conversation")
        print("---------------------------------------")

        try:
            while True:
                try:
                    user_input = input("\nYou: ").strip()
                    
                    if user_input.lower() == 'exit':
                        break
                    elif user_input.lower() == 'clear':
                        self.messages = []
                        print("\nConversation cleared.")
                        continue
                    elif not user_input:
                        continue

                    self.messages.append({
                        "role": "user",
                        "content": [{"type": "text", "text": user_input}],
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

                except KeyboardInterrupt:
                    print("\nUse 'exit' to quit or continue with your next message.")
                    continue

        except KeyboardInterrupt:
            print("\nGoodbye!")
            sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Terminal interface for computer control")
    parser.add_argument("--api-key", help="Anthropic API key")
    parser.add_argument("--provider", default="anthropic", choices=["anthropic", "bedrock", "vertex"],
                        help="API provider (default: anthropic)")
    parser.add_argument("--model", help="Model to use (defaults to provider's default)")
    parser.add_argument("--hide-images", action="store_true", help="Don't notify about screenshots")
    args = parser.parse_args()

    interface = TerminalInterface(
        api_key=args.api_key,
        provider=args.provider,
        model=args.model,
        hide_images=args.hide_images,
    )

    asyncio.run(interface.run())

if __name__ == "__main__":
    main()