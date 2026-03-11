import os
import streamlit as st
from google import genai

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
MODEL_NAME = os.getenv("MODEL_NAME", "claude-sonnet-4-5@20250929")

st.set_page_config(page_title="Claude AI Chat", page_icon="🤖")
st.title("🤖 Claude AI Chat")

if not PROJECT_ID:
    st.error("没有检测到 GOOGLE_CLOUD_PROJECT 环境变量。")
    st.stop()

client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("请输入你的问题")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Claude 思考中..."):
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