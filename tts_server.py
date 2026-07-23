import pyttsx3
from mcp.server.fastmcp import FastMCP
import subprocess
import sys

mcp=FastMCP("tts-server")

@mcp.tool()
def speak_text(text:str) -> str:
    """Converts the given text to speech and plays it aloud though the computers speakers,
    Use this too speak the final answer to the user"""

    # Ask Windows itself to speak the text, using PowerShell's built-in
    # speech synthesizer — no Python speech library needed at all.
    safe_text = text.replace('"', "'")  # avoid breaking the command
    command = f'Add-Type -AssemblyName System.Speech; ' \
              f'(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{safe_text}")'

    subprocess.run(["powershell", "-Command", command])
    return "SPOKEN"
if __name__=="__main__":
    mcp.run()

