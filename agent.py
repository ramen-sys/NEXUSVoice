import asyncio
import os
import json
from dotenv import load_dotenv
from groq import Groq,BadRequestError
from mcp import ClientSession
from mcp.client.stdio import stdio_client
import string
from datetime import datetime
from mcp_helper import DB_SERVER_PARAMS,WEB_SERVER_PARAMS, get_available_tools,call_mcp_tool
from mcp import StdioServerParameters
load_dotenv()

groq_client=Groq(api_key=os.environ.get("GROQ_API_KEY"))

WHISPER_SERVER_PARAMS=StdioServerParameters(command='python',args=["whisper_server.py"])
TTS_SERVER_PARAMS=StdioServerParameters(command='python',args=['tts_server.py'])

SYSTEM_PROMPT=(
    "you are an  expert internal IT helpdesk assistant. your core objective is to provide accurate step-by-step troubleshooting and technical solutions to users IT issues." 
    "Success means providing a clear, actionable resolution without guessing, while strictly prioritizing internal company knowledge over public web data when a tool returns"
    "You must strictly follow this sequential pipeline for every user query:"
    "1. INTERNAL DB SEARCH (Priority 1): Always query the internal database first using relevant keywords from the user's issue."
    "2. EVALUATE DB RESULTS: Analyze the database return. "
    "- If a direct match, exact solution, or official company policy is found, use it to form the answer. Stop here."
    "- If the database returns no results, or if the solution is completely irrelevant or outdated, proceed to Step 3."
    "3. WEB SEARCH FALLBACK (Priority 2): Only trigger the web search tool if Step 1 and 2 yield no viable solution. Use web search to find verified documentation (e.g., official Microsoft, Apple, Cisco, or SaaS vendor support pages. when the user says stop, then stop the process"
)
def call_groq_with_retry(messages,tools=None,max_retries=2):
    for attempt in range(max_retries+1):
        try:
            kwargs={
                "model":'llama-3.3-70b-versatile',
                "messages":messages,
                "temperature":0
            }
            if tools:
                kwargs["tools"]=tools
                kwargs["tool_choice"]='auto'
            return groq_client.chat.completions.create(**kwargs)
        except BadRequestError as e:
            if "tool_use_failed" in str(e) and attempt<max_retries:
                print(f'[Tool call fomatting glitch, retrying.. attempt {attempt +1}]')
                continue
            raise

async def handle_question(user_question:str,db_session,web_session,tts_session):
    current_datetime=datetime.now().strftime("%A, %B %d, %Y, %I:%M %p")
    messages=[
        {"role":"system","content":SYSTEM_PROMPT + f"\n\nCurrent date and time: {current_datetime}."},
        {"role":"user","content":user_question}
    ]
    db_tools= await get_available_tools(db_session)
    response=call_groq_with_retry(messages,tools=db_tools)
    reply=response.choices[0].message

    if not reply.tool_calls:
        answer=reply.content
    else:
        messages.append({
            "role":'assistant',
            "content":reply.content,
            "tool_calls":[
                {"id":tc.id,"type":"function","function":{"name":tc.function.name,"arguments":tc.function.arguments}}
                for tc in reply.tool_calls
            ]

        })

        tool_call=reply.tool_calls[0]
        tool_args=json.loads(tool_call.function.arguments)
        print(f"[Calling DB tool with :{tool_args}]")
        db_result=await call_mcp_tool(db_session,"query_staff",tool_args)

        messages.append({"role":"tool","tool_call_id":tool_call.id,"content":db_result})

        if db_result.strip()=="NO_RESULTS":
            print("[DB had nothing ,falling back to web search]")
            web_result= await call_mcp_tool(web_session,"web_search",{"query":user_question})
            messages.append({
                "role":"user",
                "content":f"The internal database had no results. Here is information from a web search instead :\n{web_result}"

            })
        print("--- Messages before final answer ---")
        for m in messages:
            print(m)
        print("--- end ---")
        final_response=call_groq_with_retry(messages)
        answer=final_response.choices[0].message.content

    print("Final answer: ",answer)
    await call_mcp_tool(tts_session,"speak_text",{"text":answer})

async def main():
    async with stdio_client(WHISPER_SERVER_PARAMS) as (wr,ww):
        async with ClientSession(wr,ww) as whisper_session:
            await whisper_session.initialize()

            async with stdio_client(DB_SERVER_PARAMS) as (dr,dw):
                async with ClientSession(dr,dw) as db_session:
                    await db_session.initialize()

                    async with stdio_client(WEB_SERVER_PARAMS) as (webr,webw):
                        async with ClientSession(webr,webw) as web_session:
                            await web_session.initialize()

                            async with stdio_client(TTS_SERVER_PARAMS) as (tr,tw):
                                async with ClientSession(tr,tw) as tts_session:
                                    await tts_session.initialize()

                                    print("Voice agent ready, say 'exit', or 'stop' to quit" )

                                    while True:
                                        result=await call_mcp_tool(whisper_session,"transcribe_audio",{})

                                        if result=="NO_SPEECH_DETECTED" or result.startswith("Error executing tool") or "WinError" in result:
                                            print(f"[ Whisper failed or No speech detected, try again] : {result}")
                                            continue
                                        cleaned=result.strip().lower().translate(str.maketrans('','',string.punctuation))
                                        if cleaned in ["exit","stop","quit"]:
                                            print("Good Bye")
                                            break
                                        # if result.strip().lower() in ["exit","stop","quit"]:
                                        #     print("Goodbye")
                                        #     break
                                        try:
                                            await handle_question(result, db_session, web_session, tts_session)
                                        except Exception as e:
                                            print(f"[Error handling question: {e}]")
                                            error_message = "Sorry, I had trouble processing that. Could you try asking again?"
                                            await call_mcp_tool(tts_session, "speak_text", {"text": error_message})

                                        

# async def run_agent(user_question:str):
#     #OPening both sessions at once
#     async with stdio_client(DB_SERVER_PARAMS) as (db_read,db_write):
#         async with ClientSession(db_read,db_write) as db_session:
#             await db_session.initialize()

#             async with stdio_client(WEB_SERVER_PARAMS) as (web_read,web_write):
#                 async with ClientSession(web_read,web_write) as web_session:
#                     await web_session.initialize()

#                     db_tools=await get_available_tools(db_session)
#                     messages=[
#                         {"role":"system",
#                          "content":("You are an internal IT helpdesk assistant. When a tool returns "
#                             "information about a staff member, you MUST base your answer strictly "
#                             "on that tool result, even if the name matches a famous or well-known "
#                             "person you know about from elsewhere. Never substitute your own "
#                             "general knowledge for tool data about staff members. If the tool "
#                             "returns NO_RESULTS and no web search result is provided either, "
#                             "say you don't have that information — do not guess."
                             
#                          )},
#                         {"role":"user","content":user_question}]
#                     response=call_groq_with_retry(messages,tools=db_tools)
#                     #letting groq decide if a tool is needed

#                     reply=response.choices[0].message

#                     if not reply.tool_calls:
#                         #Groq didnt think this needed the DB at all
#                         print("Final answer: ")
#                         return
#                     messages.append({
#                         "role": "assistant",
#                         "content": reply.content,
#                         "tool_calls": [
#                             {
#                                 "id": tc.id,
#                                 "type": "function",
#                                 "function": {
#                                     "name": tc.function.name,
#                                     "arguments": tc.function.arguments
#                                 }
#                             }
#                             for tc in reply.tool_calls
#                         ]
#                     })

#                     #executing the db tool call
#                     tool_call=reply.tool_calls[0]
#                     tool_args=json.loads(tool_call.function.arguments)

#                     print(f"[Calling DB tool with: {tool_args}]")
#                     db_result=await call_mcp_tool(db_session,"query_staff",tool_args)

#                     messages.append({
#                         "role":"tool",
#                         "tool_call_id":tool_call.id,
#                         "content":db_result
#                     })
#                     #checking if fallback is needed or not
#                     if db_result.strip()=="NO_RESULTS":
#                         print("[DB had nothing , falling back to web search]")

#                         web_result=await call_mcp_tool(web_session,"web_search",{"query":user_question})
#                         #add the web result as a new tool-style message so groq has both attempts in context for its final anser
#                         messages.append({
#                             'role':"user",
#                             "content":f"the internal database had no result Here is the information from the web search instead {web_result}"
#                         })
#                     print("Messages being sent for final answer:")
#                     for m in messages:
#                         print(m)
#                     final_response=call_groq_with_retry(messages)
#                     print("Final answer is: ",final_response.choices[0].message.content)

if __name__=="__main__":
    asyncio.run(main())

                    


           