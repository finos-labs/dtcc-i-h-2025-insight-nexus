import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from datetime import timedelta


async def test_execute_sql_query(session, query="SELECT DISTINCT details FROM corporate_actions LIMIT 100"):
    print(f"\nTesting execute_sql_query with query: {query}...")
    try:
        params = {"query": query}
        result = await session.call_tool("execute_sql_query", params)
        print("Result:", result)
        # print("Status: SUCCESS" if result and not result.startswith("Error") else "Status: FAILED")
    except Exception as e:
        print(f"Error: {e}")
        print("Status: FAILED")


async def main():
    print("Connecting to server at http://0.0.0.0:8902/mcp...")
    try:
        async with streamablehttp_client(
            url="http://0.0.0.0:8902/mcp",
            timeout=timedelta(seconds=30),
            sse_read_timeout=timedelta(seconds=300),
            terminate_on_close=True
        ) as (read, write, get_session_id):
            async with ClientSession(read, write) as session:
                print("Initializing session...")
                await session.initialize()
                print("Session initialized successfully.")
                await test_execute_sql_query(session)
                # await test_list_stock_symbols(session)
                # await test_get_stock_data(session, dataset="prices", symbol="AAPL")
                # await test_query_stock_data(session, dataset="prices", symbol="AAPL", column="symbol", value="AAPL")
                # await test_get_stock_summary(session, dataset="prices", symbol="AAPL")
            print("\nAll tests completed.")
    except Exception as e:
        print(f"Connection or session error: {e}")
        print("Status: FAILED")

if __name__ == "__main__":
    try:
        # Check if an event loop is already running
        loop = asyncio.get_running_loop()
        # If this succeeds, we're in a running loop (e.g., Spyder, Jupyter)
        loop.create_task(main())
    except RuntimeError:
        # No running loop, safe to use asyncio.run (e.g., command line)
        asyncio.run(main())
