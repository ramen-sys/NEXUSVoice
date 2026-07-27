from mcp.server.fastmcp import FastMCP
from ddgs import DDGS
import os
import sys
import requests
from dotenv import load_dotenv

mcp = FastMCP("web-server")
load_dotenv()
SERPER_API_KEY=os.environ.get("SERPER_API_KEY")


@mcp.tool()
def web_search(query: str) -> str:
    """
    Searches the web for information not found in the internal staff database.
    Use this ONLY when the question is unrelated to IT staff, on-call schedules,
    extensions, or departments — for example, general knowledge questions,
    current events, or technical troubleshooting steps not tied to a specific
    staff member.
    query should be a short, clear search phrase.
    """
    try:
        response=requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY":SERPER_API_KEY,"Content-Type":"application/json"},
            json={"q":query},
            timeout=10

        )
        response.raise_for_status()
        data=response.json()
    except Exception as e:
        return f"WEB_SEARC_ERROR: {e}"
    organic_results = data.get("organic", [])[:3]

    if not organic_results:
        return "NO_RESULTS"

    formatted = []
    for r in organic_results:
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        formatted.append(f"{title}: {snippet}")

    return "\n\n".join(formatted)
    


if __name__ == "__main__":
    mcp.run()