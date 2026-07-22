import asyncio
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params=StdioServerParameters(
        command="python",
        args=['tts_server.py']

    )
    async with stdio_client(server_params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()

            tools=await session.list_tools()
            print("Available tools: ",[t.name for t in tools.tools])

            result= await session.call_tool(
                "speak_text",
                arguments={"text":"Hello this is a test of the text to speech system"}

            )
            print("Result: ", result.content[0].text)

if __name__=="__main__":
    asyncio.run(main())

