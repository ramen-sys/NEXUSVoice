import sounddevice as sd
from scipy.io.wavfile import write

from mcp.server.fastmcp import FastMCP
import whisper
import sys
import numpy as np


mcp=FastMCP("whisper-server")

model=whisper.load_model("small")


SAMPLE_RATE=16000 #whisper expects 16khz audio
CHUNK_DURATION=0.5
SILENCE_THRESHOLD=100
SILENCE_LIMIT=1.2
MAX_DURATION=15


@mcp.tool()
def transcribe_audio() -> str:
    '''
    Records Audio from microphone for 5 seconds and transcribes it to to text using 
    local whisper model, Use this to capture what the user is asking via voice'''

    print("[Listening.... Speak now]",file=sys.stderr)

    chunk_samples=int(CHUNK_DURATION*SAMPLE_RATE)
    recorded_chunks=[]
    silence_time=0.0
    total_time=0.0
    started_speaking=False
    stream=sd.InputStream(samplerate=SAMPLE_RATE,channels=1,dtype="int16")
    with stream:
        while total_time<MAX_DURATION:
            chunk,_=stream.read(chunk_samples)
            recorded_chunks.append(chunk)
            total_time+=CHUNK_DURATION 
            volume=np.abs(chunk).mean()
            if volume>=SILENCE_THRESHOLD:
                started_speaking=True
                silence_time=0.0
            else:
                silence_time+=CHUNK_DURATION
            if started_speaking and silence_time>=SILENCE_LIMIT:
                break
    if not started_speaking:
        print("[Silence Detected, no speech]",file=sys.stderr)
        return "NO_SPEECH_DETECTED"

    recording=np.concatenate(recorded_chunks,axis=0)
    write("temp_recording.wav",SAMPLE_RATE,recording)

   

    result=model.transcribe("temp_recording.wav",language="en")
    transcribed_text=result["text"].strip()

    if not transcribed_text:
        return "NO_SPEECH_DETECTED"


    print(f'[Transcribed: {transcribed_text}]',file=sys.stderr)
    return transcribed_text


if __name__=="__main__":
    mcp.run()
