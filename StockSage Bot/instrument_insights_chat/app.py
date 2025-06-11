import streamlit as st
import json
from session import run_session
from utils import safe_async_run

# Streamlit page configuration
st.set_page_config(page_title="StockSage", layout="wide")

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tool_error" not in st.session_state:
    st.session_state.tool_error = False
if "failed_tool" not in st.session_state:
    st.session_state.failed_tool = None
if "user_message_displayed" not in st.session_state:
    st.session_state.user_message_displayed = False
if "chat_started" not in st.session_state:
    st.session_state.chat_started = False

# CSS styles (unchanged)
st.markdown("""
<style>
.stApp {
    background: 
        linear-gradient(to bottom right, #0a101b, #020510),
        radial-gradient(at top left, #0a101b, transparent 70%),
        radial-gradient(at top right, #050b14, transparent 70%),
        radial-gradient(at bottom left, #050b14, transparent 70%),
        radial-gradient(at bottom right, #020510, transparent 70%);
    background-blend-mode: screen;
    background-size: cover;
    background-repeat: no-repeat;
    background-attachment: fixed;
    color: #ffffff;
    font-family: Arial, sans-serif;
}
.chat-message { 
    padding: 1rem; 
    border-radius: 10px; 
    margin-bottom: 1rem; 
    max-width: 50%;
    margin-left: 5rem;   
    margin-right: 5rem;
    opacity: 1 !important;
}
.user-message { 
    background-color: #2b313e; 
    margin-left: auto; 
}
.assistant-message { 
    background-color: #1a1a1a; 
    margin-right: auto; 
}
.stChatInput, [data-testid="stChatInput"] {
    width: 65% !important;
    margin: 0 auto !important;
    padding: 0 !important;
    background-color: transparent !important;
    box-shadow: none !important;
    border: none !important;
}
.stChatInput textarea, [data-testid="stChatInput"] textarea {
    background-color: #1e1e1e !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 30px !important;
    min-height: 74px !important;
    max-height: 146px !important;
    font-size: 16px !important;
    font-weight: 400 !important;
    font-family: Arial, sans-serif !important;
    padding: 25px 30px !important;
    resize: none !important;
    box-shadow: inset 0 0 0 1px #333 !important;
    box-sizing: border-box !important;
    line-height: 1.5 !important;
    overflow-y: auto !important;
}
.stChatInput textarea::placeholder, [data-testid="stChatInput"] textarea::placeholder {
    color: #888 !important;
}
.stChatInput div[role="button"], [data-testid="stChatInput"] div[role="button"] {
    display: none !important;
}
.header { 
    text-align: center; 
    padding: 0; 
    font-size: 2.5rem; 
    font-weight: bold; 
}
.intro-text { 
    text-align: center; 
    padding: 0 0 2rem; 
}
button[kind="secondary"] {
    height: 100px !important;
    white-space: normal !important;
    padding: 0.5rem !important;
    font-size: 14px !important;
    line-height: 1.3 !important;
}
</style>
""", unsafe_allow_html=True)

# Default questions
default_questions = [
    "What is a brief overview of Google LLC?",
    "What are the recent price trends for AAPL from 2025-01-01 to 2025-06-01?",
    "What is the impact of dividend actions on AAPL's stock price in 2024?",
    "Can you compare the closing prices of AAPL and MSFT from 2024-12-01 to 2024-12-31?",
]

# Display a message in the chat
def display_message(message, container):
    role = message.get("role", "assistant")
    raw_content = message.get("content")

    if isinstance(raw_content, list):
        for part in raw_content:
            if "toolUse" in part or "toolResult" in part:
                return

    if isinstance(raw_content, str):
        content = raw_content
        container.markdown(
            f'<div class="chat-message {"user-message" if role == "user" else "assistant-message"}">{content.strip()}</div>',
            unsafe_allow_html=True
        )
    elif isinstance(raw_content, list):
        for part in raw_content:
            if isinstance(part, dict) and "text" in part:
                content = part["text"]
                try:
                    result_data = json.loads(content)
                    if isinstance(result_data, dict) and "plot" in result_data:
                        container.image(result_data["plot"], caption="Plot from response", use_column_width=True, output_format="PNG")
                    else:
                        container.markdown(
                            f'<div class="chat-message {"user-message" if role == "user" else "assistant-message"}">{content.strip()}</div>',
                            unsafe_allow_html=True
                        )
                except json.JSONDecodeError:
                    container.markdown(
                        f'<div class="chat-message {"user-message" if role == "user" else "assistant-message"}">{content.strip()}</div>',
                        unsafe_allow_html=True
                    )
    elif isinstance(raw_content, dict) and "text" in raw_content:
        content = raw_content["text"]
        try:
            result_data = json.loads(content)
            if isinstance(result_data, dict) and "plot" in result_data:
                container.image(result_data["plot"], caption="Plot from response", use_column_width=True, output_format="PNG")
            else:
                container.markdown(
                    f'<div class="chat-message {"user-message" if role == "user" else "assistant-message"}">{content.strip()}</div>',
                    unsafe_allow_html=True
                )
        except json.JSONDecodeError:
            container.markdown(
                f'<div class="chat-message {"user-message" if role == "user" else "assistant-message"}">{content.strip()}</div>',
                unsafe_allow_html=True
            )
            
# Header component
with st.container():
    st.markdown('<div class="header">StockSage</div>', unsafe_allow_html=True)


with st.container():
    st.markdown("""
    <div class="intro-text">
        <strong>Discover StockSage:</strong> Your ultimate companion for stock research and insights!<br>
        Unlock financials, trends, and corporate insights!
    </div>
    """, unsafe_allow_html=True)

# Main chat area
chat_container = st.container()

# Render chat history
with chat_container:
    for message in st.session_state.messages:
        display_message(message, st)

# Retry logic
if st.session_state.tool_error and st.session_state.failed_tool:
    with st.container():
        if st.button(f"Retry {st.session_state.failed_tool}"):
            st.session_state.user_message_displayed = False
            async def stream_retry():
                async for message, updated_messages, tool_error, failed_tool in run_session(
                    "", st.session_state.messages, retry_tool=st.session_state.failed_tool
                ):
                    if message.get("role") == "user" and st.session_state.user_message_displayed:
                        continue
                    with chat_container:
                        display_message(message, st)
                    st.session_state.messages = updated_messages
                    st.session_state.tool_error = tool_error
                    st.session_state.failed_tool = failed_tool
            safe_async_run(stream_retry())
            st.rerun()

# Chat input
user_input = st.chat_input("Type your message...")

# Stream response for typed input
if user_input:
    st.session_state.chat_started = True
    user_message = {"role": "user", "content": [{"text": user_input}]}
    st.session_state.messages.append(user_message)
    with chat_container:
        display_message(user_message, st)
    st.session_state.user_message_displayed = True

    async def stream_response():
        async for message, updated_messages, tool_error, failed_tool in run_session(
            user_input, st.session_state.messages
        ):
            if message.get("role") == "user" and st.session_state.user_message_displayed:
                continue
            with chat_container:
                display_message(message, st)
            st.session_state.messages = updated_messages
            st.session_state.tool_error = tool_error
            st.session_state.failed_tool = failed_tool
        st.session_state.user_message_displayed = False

    safe_async_run(stream_response())
    st.rerun()