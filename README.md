# 🎙️ NEXUS Voice MCP-Powered IT Helpdesk Voice Agent

A fully local, voice-driven IT helpdesk assistant built on the Model Context Protocol (MCP). 
Speak a question, and the agent transcribes it, checks an internal staff database first, 
falls back to a live web search only when needed, and speaks the answer back — all running 
on your own machine, no cloud voice APIs required.

## How it works

1. **Voice input** — OpenAI Whisper (running locally) transcribes your spoken question, 
   with automatic silence detection so it stops recording naturally.
2. **Reasoning** — Groq's Llama 3.3 70B model decides whether the question needs internal 
   staff data or general knowledge.
3. **Database-first lookup** — A Postgres (Neon) database of staff, roles, on-call schedules, 
   and extensions is checked first, via an MCP tool.
4. **Web fallback** — If nothing relevant is found internally, a Serper.dev-powered web 
   search tool fills the gap — automatically, without the user needing to ask twice.
5. **Voice output** — The final answer is spoken aloud through the system's speech engine.
6. **Web UI** — A React-based front end (served locally via FastAPI) shows the conversation 
   as chat bubbles, with a tag showing whether each answer came from the database, the web, 
   or the model directly.

## Architecture

Every capability (transcription, database lookup, web search, speech output) is built as an 
independent **MCP server** — a self-describing tool that any MCP-compatible LLM client can 
discover and call. The agent itself is just an MCP client that lets Groq decide, at runtime, 
which tools to use for a given question.

## Tech stack
- **LLM:** Groq (Llama 3.3 70B) — free tier, fast inference
- **Voice-to-text:** OpenAI Whisper (local)
- **Database:** Postgres via Neon (serverless, free tier)
- **Web search:** Serper.dev
- **Text-to-speech:** Windows SAPI5 (via PowerShell)
- **Protocol:** MCP (Model Context Protocol) — Python SDK
- **Frontend:** React (via CDN) + FastAPI

## Setup
1. `pip install -r requirements.txt`
2. Create a `.env` file with `GROQ_API_KEY`, `DATABASE_URL`, and `SERPER_API_KEY`
3. Run `uvicorn app:app --reload`
4. Open `http://localhost:8000`

## What I learned building this
- Designing tools with clear, LLM-readable descriptions matters as much as the code itself — 
  it's literally how the model decides what to call and when.
- Small model output glitches in structured tool-calling are real and need retry logic, 
  even from strong free-tier models.
- Local-first voice AI (Whisper + local TTS) is genuinely viable for personal/internal tools, 
  with zero per-query cost.
