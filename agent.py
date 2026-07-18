import asyncio
import os
import json
from dotenv import load_dotenv
from groq import Groq
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from mcp_helper import DUMMY_SERVER_PARAMS, get_available_tools,call_mcp_tool
load_dotenv()

groq_client=Groq(api_key=os.environ.get("GROQ_API_KEY"))

async def run_agent(user_question:str):
    #connect to the dummy MCP server 
    async with stdio_client(DUMMY_SERVER_PARAMS) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()

            #Get the tool list already converted to Groq's Format

            tools=await get_available_tools(session)

            messages=[{"role":"user","content":user_question}]
            print("Tools being sent to Groq:", json.dumps(tools, indent=2))

            response=groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=tools,
                tool_choice="auto"#letting groq decide if a tool is needed

            )
            reply=response.choices[0].message

            #check if groq wants to call a tool
            if reply.tool_calls:
                #groq can request multiple tools calls we handle them one by one
                messages.append(reply)

                for tool_call in reply.tool_calls:
                    tool_name=tool_call.function.name
                    tool_args=json.loads(tool_call.function.arguments)

                    print(f"[Groq decided to call tool:{tool_name}]")

                    #Actually execute the tool via MCP

                    tool_result=await call_mcp_tool(session,tool_name,tool_args)

                    messages.append({
                        "role":'tool',
                        "tool_call_id":tool_call.id,
                        "content":tool_result

                    })

                #Ask groq for the final answer,now that it has the tool result
                final_response=groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages
                )
                print("Final Answer: ",final_response.choices[0].message.content)
            else:
                print("Final answer: ",reply.content)

if __name__=="__main__":
    asyncio.run(run_agent("What time is it now"))
