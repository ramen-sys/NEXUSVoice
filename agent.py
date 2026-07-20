import asyncio
import os
import json
from dotenv import load_dotenv
from groq import Groq
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from mcp_helper import DB_SERVER_PARAMS,WEB_SERVER_PARAMS, get_available_tools,call_mcp_tool
load_dotenv()

groq_client=Groq(api_key=os.environ.get("GROQ_API_KEY"))

async def run_agent(user_question:str):
    #OPening both sessions at once
    async with stdio_client(DB_SERVER_PARAMS) as (db_read,db_write):
        async with ClientSession(db_read,db_write) as db_session:
            await db_session.initialize()

            async with stdio_client(WEB_SERVER_PARAMS) as (web_read,web_write):
                async with ClientSession(web_read,web_write) as web_session:
                    await web_session.initialize()

                    db_tools=await get_available_tools(db_session)
                    messages=[{"role":"user","content":user_question}]
                    response=groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        temperature=0,
                        messages=messages,
                        tools=db_tools,
                        tool_choice="auto")#letting groq decide if a tool is needed

                    reply=response.choices[0].message

                    if not reply.tool_calls:
                        #Groq didnt think this needed the DB at all
                        print("Final answer: ")
                        return
                    messages.append({
                        "role": "assistant",
                        "content": reply.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in reply.tool_calls
                        ]
                    })

                    #executing the db tool call
                    tool_call=reply.tool_calls[0]
                    tool_args=json.loads(tool_call.function.arguments)

                    print(f"[Calling DB tool with: {tool_args}]")
                    db_result=await call_mcp_tool(db_session,"query_staff",tool_args)

                    messages.append({
                        "role":"tool",
                        "tool_call_id":tool_call.id,
                        "content":db_result
                    })
                    #checking if fallback is needed or not
                    if db_result.strip()=="NO_RESULTS":
                        print("[DB had nothing , falling back to web search]")

                        web_result=await call_mcp_tool(web_session,"web_search",{"query":user_question})
                        #add the web result as a new tool-style message so groq has both attempts in context for its final anser
                        messages.append({
                            'role':"user",
                            "content":f"the internal database had no result Here is the information from the web search instead {web_result}"
                        })
                    print("Messages being sent for final answer:")
                    for m in messages:
                        print(m)
                    final_response=groq_client.chat.completions.create(model="llama-3.3-70b-versatile",messages=messages)
                    print("Final answer is: ",final_response.choices[0].message.content)

if __name__=="__main__":
    asyncio.run(run_agent("Who is Ayesha Malik ?"))

                    


           