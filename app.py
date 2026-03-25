import os
import tempfile
import streamlit as st
from anthropic import AnthropicVertex

st.set_page_config(page_title="Claude AI Chat", page_icon="🤖")
st.title("🤖 Claude AI Chat")
st.caption("Streamlit Cloud + Vertex AI + Claude")

# 从 Streamlit secrets 读取 GCP 凭证
if "GOOGLE_CREDENTIALS" in st.secrets:
    creds = st.secrets["GOOGLE_CREDENTIALS"]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    tmp.write(creds.encode("utf-8"))
    tmp.close()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name

PROJECT_ID = st.secrets.get("GOOGLE_CLOUD_PROJECT", "")
REGION = st.secrets.get("GOOGLE_CLOUD_LOCATION", "global")

st.write("DEBUG PROJECT_ID =", PROJECT_ID)

if not PROJECT_ID:
    st.error("没有检测到 GOOGLE_CLOUD_PROJECT")
    st.stop()

try:
    client = AnthropicVertex(project_id=PROJECT_ID, region=REGION)
except Exception as e:
    st.error(f"Vertex 客户端初始化失败：{e}")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("参数设置")
    system_prompt = st.text_area(
        "System Prompt",
        value="你是一个简洁、准确、乐于助人的 AI 助手。",
        height=120,
    )
    max_tokens = st.slider("Max tokens", 128, 1024, 256, 64)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.1)

    if st.button("清空对话"):
        st.session_state.messages = []
        st.rerun()

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
                api_messages = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[-2:]
                ]

                response = client.messages.create(
                    model="claude-sonnet-4-6",
                    system=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=api_messages,
                )

                reply = "".join(
                    block.text for block in response.content
                    if getattr(block, "type", None) == "text"
                ).strip()

                if not reply:
                    reply = "模型没有返回可显示的文本内容。"

                st.markdown(reply)

            except Exception as e:
                reply = f"调用失败：{e}"
                st.error(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})