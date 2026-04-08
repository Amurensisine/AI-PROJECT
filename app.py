import os
import time
import tempfile
import streamlit as st
from anthropic import AnthropicVertex

st.set_page_config(page_title="Claude AI Chat", page_icon="&#x1F916;")
st.title("&#x1F916; Claude AI Chat")
st.caption("Streamlit Cloud + Vertex AI + Claude")

# Read GCP credentials from Streamlit secrets
if "GOOGLE_CREDENTIALS" in st.secrets:
    creds = st.secrets["GOOGLE_CREDENTIALS"]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    tmp.write(creds.encode("utf-8"))
    tmp.close()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name

PROJECT_ID = st.secrets.get("GOOGLE_CLOUD_PROJECT", "")
REGION = st.secrets.get("GOOGLE_CLOUD_LOCATION", "us-central1")

with st.expander("DEBUG", expanded=False):
    st.write("PROJECT_ID =", PROJECT_ID)
    st.write("REGION =", REGION)

if not PROJECT_ID:
    st.error("GOOGLE_CLOUD_PROJECT not found. Please set it in Streamlit Cloud Secrets.")
    st.stop()

# Initialize Vertex client
@st.cache_resource
def get_client():
    return AnthropicVertex(project_id=PROJECT_ID, region=REGION)

try:
    client = get_client()
except Exception as e:
    st.error(f"Vertex client init failed: {e}")
    st.stop()

MODEL = "claude-haiku-4-5"

# API call with retry on 429
def call_claude(messages, system_prompt, max_tokens, temperature, retries=3):
    for attempt in range(retries):
        try:
            response = client.messages.create(
                model=MODEL,
                system=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
            )
            return "".join(
                block.text for block in response.content
                if getattr(block, "type", None) == "text"
            ).strip() or "No response from model."

        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                if attempt < retries - 1:
                    wait = 2 ** attempt
                    st.warning(f"Rate limit hit, retrying in {wait}s ({attempt + 1}/{retries})...")
                    time.sleep(wait)
                    continue
                return "Rate limit exceeded (429). Please try again later."
            return f"API call failed: {e}"

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.header("Settings")
    system_prompt = st.text_area(
        "System Prompt",
        value="You are a helpful, concise AI assistant.",
        height=120,
    )
    max_tokens = st.slider("Max tokens", 128, 1024, 256, 64)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.1)
    st.caption(f"Model: `{MODEL}`")

    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input
user_input = st.chat_input("Type your message here")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            raw = st.session_state.messages[-10:]
            while raw and raw[0]["role"] != "user":
                raw = raw[1:]

            api_messages = [
                {"role": m["role"], "content": m["content"]}
                for m in raw
            ]

            reply = call_claude(api_messages, system_prompt, max_tokens, temperature)
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
