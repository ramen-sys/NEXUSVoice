import json
from contextlib import AsyncExitStack
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from mcp_helper import DB_SERVER_PARAMS,WEB_SERVER_PARAMS,get_available_tools,call_mcp_tool
from agent import WHISPER_SERVER_PARAMS,TTS_SERVER_PARAMS,SYSTEM_PROMPT,call_groq_with_retry

from datetime import datetime

app=FastAPI()
sessions={}
exit_stack=AsyncExitStack()

@app.on_event("startup")
async def startup():
    async def open_session(params):
        read,write=await exit_stack.enter_async_context(stdio_client(params))
        session=await exit_stack.enter_async_context(ClientSession(read,write))
        await session.initialize()
        return session

    sessions["whisper"]=await open_session(WHISPER_SERVER_PARAMS)
    sessions["db"]=await open_session(DB_SERVER_PARAMS)
    sessions["web"]=await open_session(WEB_SERVER_PARAMS)
    sessions["tts"]=await open_session(TTS_SERVER_PARAMS)
    print("TTS session ready:", sessions["tts"])
    print("ALL MCP SESSIONS READY")


@app.on_event("shutdown")
async def shutdown():
    await exit_stack.aclose()

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.post("/ask")
async def ask():
    question=await call_mcp_tool(sessions["whisper"],"transcribe_audio",{})

    if question=="NO_SPEECH_DETECTED" or "WinError" in question or question.startswith("Error"):
        return JSONResponse({"question":"","answer":"I didn't catch that, try again","source":"none"})
    current_datetime=datetime.now().strftime("%A, %B %d, %Y, %I:%M %p")
    messages=[
        {"role":"system","content":SYSTEM_PROMPT+ F"\n\nCurrent date and time :{current_datetime}."},
        {"role":"user","content":question}

    ]

    db_tools=await get_available_tools(sessions["db"])
    response=call_groq_with_retry(messages,tools=db_tools)
    reply=response.choices[0].message

    source="none"

    if not reply.tool_calls:
        answer=reply.content
    else:
        messages.append({
            "role":"assistant",
            "content":reply.content,
            "tool_calls":[ 
                {"id":tc.id,"type":"function",
                "function":{"name":tc.function.name,"arguments":tc.function.arguments}}
                for tc in reply.tool_calls
            ]
        
        })
        tool_call=reply.tool_calls[0]
        tool_args=json.loads(tool_call.function.arguments)
        db_result=await call_mcp_tool(sessions["db"],"query_staff",tool_args)
        messages.append({"role":"tool","tool_call_id":tool_call.id,"content":db_result})

        source="database"

        if db_result.strip()=="NO_RESULTS":
            source="web"
            web_result=await call_mcp_tool(sessions["web"],"web-search",{"query":question})
            messages.append({
                "role":"user",
                "content":f"the internal database had no result here is information from the web instead:\n {web_result}"

            })
        final_response=call_groq_with_retry(messages)
        answer=final_response.choices[0].message.content

        await call_mcp_tool(sessions["tts"],"speak_test",{"text":answer})

    return JSONResponse({"question":question,"answer":answer,"source":source})

