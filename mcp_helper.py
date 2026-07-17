from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


DUMMY_SERVER_PARAMS=StdioServerParameters(
    command="python",
    args=["dummy_server.py"]
)#this tell our client how to launch our dummy server as a subprocess

def mcp_tool_to_groq_format(mcp_tool):
    """converts a single mcp tool description into the JSON shape Groqs API expects
    for its tools parameters"""

    return {
        "type":"function",
        "function":{
            "name":mcp_tool.name,
            "description": mcp_tool.description or "",
            "parameters":mcp_tool.inputSchema or {"type":"object","properties":{}}

    
        }
    }

async def get_available_tools(session:ClientSession):
    """Asks MCP server what tools it has then converts it into Groqs Expected Format"""

    tools_response=await session.list_tools()
    return [mcp_tool_to_groq_format(tool) for tool in tools_response.tools]

async def call_mcp_tool(session:ClientSession,tool_name:str,arguments:dict):
    """Actually executes a tool call through MCP session,
    and return just the plain text result"""

    result =await session.call_tool(tool_name,arguments=arguments)
    return result.content[0].texts
