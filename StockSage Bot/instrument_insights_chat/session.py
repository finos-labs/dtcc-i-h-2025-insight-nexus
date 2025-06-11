import asyncio
from mcp import ClientSession
from mcp.client import streamable_http
from aws_client import bedrock
from utils import convert_tool_format, validate_messages
import json
from datetime import timedelta
from typing import List, Tuple, AsyncGenerator

# Load metadata once
with open("../mcp_server/meta_data.json", "r") as f:
    metadata_context = json.load(f)

async def run_session(user_input: str, messages: List[dict], retry_tool: str = None) -> AsyncGenerator[Tuple[dict, List[dict], bool, str], None]:
    """Manages the session with a running MCP server and Bedrock API, yielding message chunks for streaming."""
    try:
        print("Attempting to connect to MCP server at http://localhost:8000/mcp...")
        async with streamable_http.streamablehttp_client(
            url="http://localhost:8000/mcp",
            timeout=timedelta(seconds=30),
            sse_read_timeout=timedelta(seconds=300),
            terminate_on_close=True
        ) as (read_stream, write_stream, get_session_id):
            print("Connected to MCP server, initializing session...")
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools_result = await session.list_tools()

                tools_list = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema,
                    }
                    for tool in tools_result.tools
                ]
                system = [
                    {
                        "text": (
                            "You are a helpful AI assistant with access to various tools to assist with user queries.\n\n"
                            "When responding:\n"
                            "- Provide only the information that directly answers the user's question — avoid extra or unrelated content.\n"
                            "- Do NOT mention the names of internal tools (e.g., 'query_stock_data'). Instead, refer to them using neutral terms like 'data retrieval processes.'\n"
                            "- Format responses flexibly: use bullet points, paragraphs, or a combination. Vary the style across the conversation to keep it dynamic and suited to the query.\n\n"
                            "Provide professional response in plain text with no formatting or emphasis, do not bold or italic any specific part of response"
                            "The list of available stocks in our database is provided in the metadata.\n\n"
                            "Available tools: " + json.dumps(tools_list) + "\n\n"
                            "Metadata context:\n" + json.dumps(metadata_context)
                        )
                    }
                ]

                if retry_tool:
                    messages.append({"role": "user", "content": [{"text": f"Retry the {retry_tool} tool."}]})

                tool_error = False
                failed_tool = None

                # Yield initial user input as a message
                if user_input:
                    yield {"role": "user", "content": [{"text": user_input}]}, messages, tool_error, failed_tool

                while True:
                    response = bedrock.converse(
                        modelId="us.anthropic.claude-3-5-haiku-20241022-v1:0", #"us.anthropic.claude-3-5-haiku-20241022-v1:0",
                        messages=validate_messages(messages),
                        system=system,
                        inferenceConfig={"maxTokens": 1000, "topP": 0.1, "temperature": 0.3},
                        toolConfig=convert_tool_format(tools_result.tools),
                    )

                    output_message = response["output"]["message"]
                    # Clean trailing colon from the last text segment
                    if (
                        "content" in output_message 
                        and isinstance(output_message["content"], list) 
                        and "text" in output_message["content"][0]
                    ):
                        output_message["content"][0]["text"] = output_message["content"][0]["text"].rstrip(":")

                    messages.append(output_message)
                    stop_reason = response["stopReason"]

                    for content in output_message["content"]:
                        if "text" in content:
                            if "error" in content["text"].lower() and "stock symbols" in content["text"].lower():
                                tool_error = True
                                failed_tool = "list_stock_symbols"
                            # Yield each text chunk as a separate message
                            yield {"role": "assistant", "content": [{"text": content["text"]}]}, messages, tool_error, failed_tool

                    if stop_reason == "tool_use":
                        for tool_req in output_message["content"]:
                            if "toolUse" in tool_req:
                                tool = tool_req["toolUse"]
                                try:
                                    tool_response = await session.call_tool(tool["name"], tool["input"])
                                    tool_result = {
                                        "toolUseId": tool["toolUseId"],
                                        "content": [{"text": str(tool_response)}],
                                    }
                                    # Yield tool response as a separate message
                                    yield {"role": "assistant", "content": [{"toolResult": str(tool_response)}]}, messages, tool_error, failed_tool
                                except Exception as err:
                                    print(f"Tool call failed: {err}")
                                    tool_error = True
                                    failed_tool = tool["name"]
                                    tool_result = {
                                        "toolUseId": tool["toolUseId"],
                                        "content": [{"text": f"Error: {str(err)}"}],
                                        "status": "error"
                                    }
                                    # Yield tool error as a separate message
                                    yield {"role": "assistant", "content": [{"toolResult": f"Error: {str(err)}"}]}, messages, tool_error, failed_tool
                                messages.append({
                                    "role": "user",
                                    "content": [{"toolResult": tool_result}]
                                })
                    else:
                        break

    except BaseExceptionGroup as eg:
        print("ExceptionGroup caught with sub-exceptions:")
        for i, exc in enumerate(eg.exceptions, 1):
            print(f"Sub-exception {i}: {type(exc).__name__}: {exc}")
            if hasattr(exc, '__cause__') and exc.__cause__:
                print(f"  Caused by: {type(exc.__cause__).__name__}: {exc.__cause__}")
            if hasattr(exc, 'response') and exc.response:
                print(f"  Response details: {exc.response}")
        raise
    except Exception as e:
        print(f"Error with streamable_http connection: {type(e).__name__}: {e}")
        if hasattr(e, '__cause__') and e.__cause__:
            print(f"  Caused by: {type(e.__cause__).__name__}: {e.__cause__}")
        raise