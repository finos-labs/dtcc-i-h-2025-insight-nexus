import json
import asyncio
import nest_asyncio
from typing import List

def convert_tool_format(tools):
    """Converts tool objects to the format expected by Bedrock API."""
    return {
        "tools": [
            {
                "toolSpec": {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": {"json": tool.inputSchema},
                }
            }
            for tool in tools
        ]
    }

def validate_messages(messages: List[dict], window_size: int = 10) -> List[dict]:
    """Validates and formats messages for Bedrock API, keeping only tool-use messages after the last user query and limiting to window_size."""
    validated = []
    
    # Step 1: Find the index of the last user query
    last_user_index = -1
    for i, msg in enumerate(messages):
        if msg.get("role") == "user" and any("text" in c for c in msg.get("content", [])):
            last_user_index = i
    
    # Step 2: Process messages
    for i, msg in enumerate(messages):
        # Convert string content to list format if needed
        if isinstance(msg["content"], str):
            content = [{"text": msg["content"]}]
        else:
            content = msg["content"]
        
        # Step 3: Filter tool-use messages
        if any("toolUse" in c or "toolResult" in c for c in content):
            # Keep tool-use messages only if they are after the last user query
            if last_user_index == -1 or i > last_user_index:
                validated.append({
                    "role": msg["role"],
                    "content": content
                })
        else:
            # Always keep user and assistant text messages
            validated.append({
                "role": msg["role"],
                "content": content
            })
    
    # Step 4: Limit to the last window_size messages
    validated = validated[-window_size:]
    
    return validated

def safe_async_run(coro):
    """Safely runs an async coroutine in a synchronous context."""
    nest_asyncio.apply()
    return asyncio.get_event_loop().run_until_complete(coro)
