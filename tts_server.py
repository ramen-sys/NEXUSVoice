import pyttsx3
from mcp.server.fastmcp import FastMCP
import subprocess

mcp=FastMCP("tts-server")

@mcp.tool()
def speak_text(text:str) -> str:
    """Converts the given text to speech and plays it aloud though the computers speakers,
    Use this too speak the final answer to the user"""

    try:
        subprocess.run(["python", "tts_helper.py", text], check=True)
        return "SPOKEN"
    except subprocess.CalledProcessError as e:
        return f"TTS_ERROR: {e}"
if __name__=="__main__":
    mcp.run()

