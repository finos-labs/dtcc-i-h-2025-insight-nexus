import argparse
from mcp.server.fastmcp import FastMCP
from resources import register_resources
from tools import register_tools

print("Starting StockDataServer...")  # Debug

# Initialize the MCP server
mcp = FastMCP("StockDataServer")

# Register resources and tools
register_resources(mcp)
register_tools(mcp)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run MCP server with optional transport"
    )
    parser.add_argument(
        "--transport",
        type=str,
        default="streamable-http",
        help="Transport method to use (stdio, sse, streamable-http)"
    )
    args = parser.parse_args()

    if args.transport in ["stdio", "sse", "streamable-http"]:
        print(f"Starting server with {args.transport} transport...")
        mcp.run(transport=args.transport)#, address="0.0.0.0")
    else:
        print(f"Error: Invalid transport '{args.transport}'. Supported: stdio, sse, streamable-http")
        exit(1)
