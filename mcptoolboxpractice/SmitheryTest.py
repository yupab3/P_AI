import mcp
from mcp.client.websocket import websocket_client
import json, os
import base64
from dotenv import load_dotenv

load_dotenv()
config = {
  "dynamic": False,
  "profile": "string",
  "transport": "stdio",
  "smitheryApiKey": "string"
}
# Encode config in base64
config_b64 = base64.b64encode(json.dumps(config).encode())
smithery_api_key = os.getenv("SMITHERY_API_KEY")

# Create server URL
url = f"wss://server.smithery.ai/@smithery/toolbox/ws?config={config_b64}&api_key={smithery_api_key}"

async def main():
    # Connect to the server using websocket client
    async with websocket_client(url) as streams:
        print (1)
        async with mcp.ClientSession(*streams) as session:
            # Initialize the connection
            print (2)
            await session.initialize()
            # List available tools
            print (3)
            tools_result = await session.list_tools()
            print(f"Available tools: {', '.join([t.name for t in tools_result.tools])}")

            # Example of calling a tool:
            # result = await session.call_tool("tool-name", arguments={"arg1": "value"})

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())