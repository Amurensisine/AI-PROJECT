import os
import tempfile
import streamlit as st
from google import genai

# ===== Google Cloud credentials from Railway Variables =====
creds = os.getenv("GOOGLE_CREDENTIALS")
if creds:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    tmp.write(creds.encode("utf-8"))
    tmp.close()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
MODEL_NAME = "publishers/anthropic/models/claude-sonnet-4-6@default"

st.set_page_config(page_title="Claude AI Chat", page_icon="🤖")
st.title("🤖 Claude AI Chat")
st.caption("ECNU 实用人工智能课程项目 · Railway + Vertex AI + Claude Sonnet 4.6")

if not PROJECT_ID:
    st.error("没有检测到 GOOGLE_CLOUD_PROJECT，请先在 Railway Variables 里配置。")
    st.stop()

# ===== Initialize Vertex AI client =====
try:
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION,
    )
except Exception as e:
    st.error(f"Vertex AI 客户端初始化失败：{e}")
    st.stop()

# ===== Session state =====
if "messages" not in st.session_state:
    st.session_state.messages = []

# ===== Sidebar =====
with st.sidebar:
    st.header("参数设置")
    system_prompt = st.text_area(
        "System Prompt",
        value="你是一个简洁、准确、乐于助人的 AI 助手。",
        height=120,
    )
    if st.button("清空对话"):
        st.session_state.messages = []
        st.rerun()

# ===== Display history =====
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ===== User input =====
user_input = st.chat_input("请输入你的问题")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Claude 思考中..."):
            try:
                # Build a simple conversation context
                conversation_text = system_prompt + "\n\n"
                for msg in st.session_state.messages:
                    role_name = "用户" if msg["role"] == "user" else "助手"
                    conversation_text += f"{role_name}: {msg['content']}\n"
                conversation_text += "助手:"

                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=conversation_text,
                )

                reply = response.text if hasattr(response, "text") else str(response)
                st.markdown(reply)

            except Exception as e:
                reply = f"调用失败：{e}"
                st.error(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})