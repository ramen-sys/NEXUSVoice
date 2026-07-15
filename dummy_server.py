from mcp.server.fastmcp import FastMCP
from datetime import datetime

mcp=FastMCP("dummy-server")

@mcp.tool()
def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if __name__=="__main__":
    mcp.run()