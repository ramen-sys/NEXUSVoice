import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params=StdioServerParameters(
        command="python",
        args=["db_server.py"]
    )

    async with stdio_client(server_params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()

            tools=await session.list_tools()
            print("Available tools",[t.name for t in tools.tools])

            result =await session.call_tool("query_staff",arguments={"question_topic":"network"})
            print("result for network: ")
            print(result.content[0].text)

            result2=await session.call_tool("query_staff",arguments={"question_topic":"plumbing"})
            print("Result for plumbing")
            print(result2.content[0].text)

if __name__ == "__main__":
    asyncio.run(main())
