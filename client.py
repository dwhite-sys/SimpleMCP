import streamlit as st
import requests
import sqlite3
import json
import groq
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), override=True)

# =====================================================================
#    CONFIG
# =====================================================================

GROQ_MODEL = "openai/gpt-oss-20b"

def get_groq_client():
    key = os.environ.get("GROQ_API_KEY")
    return groq.Groq(api_key=key)

tool_call_limit = 5
tool_calls = 0

# =====================================================================
#    LOAD SERVER IP FROM FILE (Simple MCP)
# =====================================================================

def load_server_ip():
    try:
        with open("ip_address.txt", "r") as f:
            return f.read().strip()
    except:
        return "http://127.0.0.1:8000"  # fallback default

SERVER_IP = load_server_ip()

# =====================================================================
#    LOAD TOOL SCHEMA FROM SIMPLE MCP SERVER
# =====================================================================

def load_tools():
    try:
        r = requests.get(f"{SERVER_IP}/list_tools", timeout=5)
        t = r.json().get("tools", [])
        return t
    except Exception as e:
        st.sidebar.error(f"Tool load error: {e}")
        return []

tools = load_tools()

# =====================================================================
#    TOOL EXECUTION via Simple MCP /run_tool
# =====================================================================

def run_remote_tool(tool_name: str, arguments: dict):
    """
    Calls Simple MCP FastAPI server:
    POST /run_tool { "tool": ..., "arguments": ... }
    """
    try:
        payload = {
            "tool": tool_name,
            "arguments": arguments,
        }
        r = requests.post(f"{SERVER_IP}/run_tool", json=payload, timeout=20)
        data = r.json()

        if "result" in data:
            return data["result"]
        else:
            return f"ERROR: {data.get('error', 'unknown error from server')}"

    except Exception as e:
        return f"HTTP ERROR calling tool: {e}"

# =====================================================================
#    RECURSIVE MODEL RUNNER  (PATCHED)
# =====================================================================

def run_model(messages: list):
    """
    - Calls Groq
    - Handles recursive tool calling
    - Feeds tool results back into model messages
    - PATCHED: Tool results are always JSON-serialized strings
    """
    global tool_call_limit
    global tool_calls
    while True:
        response = get_groq_client().chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=tools,
            max_tokens=2048,
        )

        msg = response.choices[0].message

        # Case 1: Final answer (no tool calls)
        if not msg.tool_calls:
            messages.append({
                "role": "assistant",
                "content": msg.content
            })
            tool_calls = 0
            return messages

        # Case 2: Model wants to call tool(s)
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": msg.tool_calls
        })

        for tool_call in msg.tool_calls:
            tool_calls += 1

            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            # === Simple MCP replacement ===
            result = run_remote_tool(name, args)

            # === IMPORTANT PATCH ===
            # Convert all tool results into a JSON string before passing to Groq
            safe_result = json.dumps(result, ensure_ascii=False)

            # Feed result back into model
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": name,
                "content": safe_result,   # <-- Now ALWAYS a string
            })
            if tool_calls >= tool_call_limit:
                messages.append({
                    "role": "tool",
                    "content": "Tool call limit reached. Stopping further tool calls."
                })
                return messages

# =====================================================================
#    STREAMLIT UI
# =====================================================================

st.set_page_config(page_title="Groq + Simple MCP", layout="wide")
st.title("⚡ Groq + Simple MCP Tools (Web + SQLite Server)")

# Sidebar for alternate servers
st.sidebar.header("Simple MCP Server")
sidebar_ip = st.sidebar.text_input("Server URL", SERVER_IP)
if sidebar_ip and sidebar_ip != SERVER_IP:
    SERVER_IP = sidebar_ip
    with open("ip_address.txt", "w") as f:
        f.write(SERVER_IP)
    tools = load_tools()  # refresh registry

# Chat history
if "chat" not in st.session_state:
    st.session_state.chat = []

prompt = st.chat_input("Message")

if prompt:
    st.session_state.chat.append({"role": "user", "content": prompt})
    st.session_state.chat = run_model(st.session_state.chat)

# Render messages
for msg in st.session_state.chat:
    if msg["role"] == "tool":
        st.chat_message("assistant").write(
            f"🛠️ **Tool result ({msg['name']}):**\n\n{msg['content']}"
        )
    else:
        st.chat_message(msg["role"]).write(msg.get("content", ""))
