from mcp.server.fastmcp import FastMCP
from ddgs import DDGS

mcp = FastMCP("web-server")


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
        results = DDGS().text(query, max_results=3)
    except Exception as e:
        return f"WEB_SEARCH_ERROR: {e}"

    if not results:
        return "NO_RESULTS"

    formatted = []
    for r in results:
        title = r.get("title", "")
        body = r.get("body", "")
        formatted.append(f"{title}: {body}")

    return "\n\n".join(formatted)


if __name__ == "__main__":
    mcp.run()