import asyncio
from mcp import ClientSession, StdioServerParameters

from mcp.client.stdio import stdio_client

async def main(): 
    '''Tell the client HOW to launch the server :run "oythin dummy_server.py'''
    server_params=StdioServerParameters(
        command="python",
        args=["dummy_server.py"]

    )
    #Launch the server as a subprocess and open a communication channel
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read,write) as session:
            await session.initialize() #handshake with the server 

            tools=await session.list_tools()#Ask the server "what tools do you have"
            print("Available Tools",[t.name for t in tools.tools])


            #call the dummy tool directly 
            result=await session.call_tool("get_current_time",arguments={})
            print("Tool result: ", result.content[0].text)

if __name__=="__main__":
    asyncio.run(main())


