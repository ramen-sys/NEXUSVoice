import sounddevice as sd
from scipy.io.wavfile import write

from mcp.server.fastmcp import FastMCP
import whisper
import sys
import numpy as np


mcp=FastMCP("whisper-server")

model=whisper.load_model("small")


SAMPLE_RATE=16000 #whisper expects 16khz audio
DURATION=5  

@mcp.tool()
def transcribe_audio() -> str:
    '''
    Records Audio from microphone for 5 seconds and transcribes it to to text using 
    local whisper model, Use this to capture what the user is asking via voice'''

    print("[Listening.... Speak now]",file=sys.stderr)
    recording=sd.rec(
        int(DURATION*SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )
    sd.wait()
    volume = np.abs(recording).mean()
    SILENCE_THRESHOLD = 100  # tune this based on testing

    if volume < SILENCE_THRESHOLD:
        print(f"[Silence detected, volume: {volume:.1f}]", file=sys.stderr)
        return "NO_SPEECH_DETECTED"


    write("temp_recording.wav",SAMPLE_RATE,recording)

    result=model.transcribe("temp_recording.wav",language="en")
    transcribed_text=result["text"].strip()

    if not transcribed_text:
        return "NO_SPEECH_DETECTED"


    print(f'[Transcribed: {transcribed_text}],file=sys.stderr')
    return transcribed_text


if __name__=="__main__":
    mcp.run()
