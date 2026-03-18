import os
import tempfile
import streamlit as st
from google import genai

creds = os.getenv("GOOGLE_CREDENTIALS")
if creds:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    tmp.write(creds.encode("utf-8"))
    tmp.close()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
MODEL_NAME = "publishers/anthropic/models/claude-sonnet-4-6"

st.set_page_config(page_title="Claude AI Chat", page_icon="🤖")
st.write("DEBUG PROJECT_ID =", PROJECT_ID)

st.title("Claude AI Chat")
st.caption("Railway + Vertex AI + Claude Sonnet 4.6")

if not PROJECT_ID:
    st.error("没有检测到 GOOGLE_CLOUD_PROJECT")
    st.stop()

client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

user_input = st.chat_input("Ask something")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Claude is thinking..."):
            try:
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=user_input,
                )
                reply = response.text
                st.markdown(reply)
            except Exception as e:
                reply = f"调用失败：{e}"
                st.error(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})