import os
import tempfile
import streamlit as st
from anthropic import AnthropicVertex

# 读取 Railway Variables 里的服务账号 JSON
creds = os.getenv("GOOGLE_CREDENTIALS")
if creds:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    tmp.write(creds.encode("utf-8"))
    tmp.close()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")

# Claude on Vertex AI 官方文档示例使用区域端点。
# 先别用 global，先用一个明确支持 Claude 的区域。
REGION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-east5")

MODEL_NAME = "claude-sonnet-4-6"

st.set_page_config(page_title="Claude AI Chat", page_icon="🤖")
st.title("🤖 Claude AI Chat")
st.caption("Railway + Vertex AI + Claude Sonnet 4.6")

if not PROJECT_ID:
    st.error("没有检测到 GOOGLE_CLOUD_PROJECT。")
    st.stop()

try:
    client = AnthropicVertex(project_id=PROJECT_ID, region=REGION)
except Exception as e:
    st.error(f"Claude Vertex 客户端初始化失败：{e}")
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
    max_tokens = st.slider("Max tokens", 128, 2048, 800, 64)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.3, 0.1)

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
                    for m in st.session_state.messages
                ]

                response = client.messages.create(
                    model=MODEL_NAME,
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