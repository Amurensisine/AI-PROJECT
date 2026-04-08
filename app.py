import os
import time
import tempfile
import streamlit as st
from anthropic import AnthropicVertex

st.set_page_config(page_title="Claude AI Chat", page_icon="🤖")
st.title("🤖 Claude AI Chat")
st.caption("Streamlit Cloud + Vertex AI + Claude")

# ── 读取 GCP 凭证 ──────────────────────────────────────────
if "GOOGLE_CREDENTIALS" in st.secrets:
    creds = st.secrets["GOOGLE_CREDENTIALS"]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    tmp.write(creds.encode("utf-8"))
    tmp.close()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name

PROJECT_ID = st.secrets.get("GOOGLE_CLOUD_PROJECT", "")
# 修复：固定使�?us-east5，该 region �?Claude 模型支持最稳定
REGION = st.secrets.get("GOOGLE_CLOUD_LOCATION", "us-east5")

# ── 调试信息（上线后可删除）──────────────────────────────────
with st.expander("🔧 DEBUG 信息", expanded=False):
    st.write("PROJECT_ID =", PROJECT_ID)
    st.write("REGION =", REGION)

if not PROJECT_ID:
    st.error("�?未检测到 GOOGLE_CLOUD_PROJECT，请�?Streamlit Cloud Secrets 中配置�?)
    st.stop()

# ── 初始�?Vertex 客户�?────────────────────────────────────
@st.cache_resource
def get_client():
    return AnthropicVertex(project_id=PROJECT_ID, region=REGION)

try:
    client = get_client()
except Exception as e:
    st.error(f"�?Vertex 客户端初始化失败：{e}")
    st.stop()

# ── 模型名称（Vertex AI 要求带版本号）──────────────────────
# claude-3-5-sonnet-v2 quota 更宽松，作为首�?# 如需更新可换�?claude-sonnet-4-5@20251205
MODEL = "claude-haiku-4-5@20251001"

# ── 带重试的 API 调用函数 ───────────────────────────────────
def call_claude(messages, system_prompt, max_tokens, temperature, retries=3):
    """
    调用 Claude，遇�?429 quota 错误时自动重试（指数退避）�?    """
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
            ).strip() or "模型没有返回可显示的文本内容�?

        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                if attempt < retries - 1:
                    wait = 2 ** attempt  # 1s �?2s �?4s
                    st.warning(f"�?Quota 限制，{wait} 秒后自动重试（{attempt + 1}/{retries}�?..")
                    time.sleep(wait)
                    continue
                return "�?请求次数超限�?29），请稍后再试�?
            return f"�?调用失败：{e}"

# ── 会话状�?────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── 侧边栏参�?──────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 参数设置")
    system_prompt = st.text_area(
        "System Prompt",
        value="你是一个简洁、准确、乐于助人的 AI 助手�?,
        height=120,
    )
    max_tokens = st.slider("Max tokens", 128, 1024, 256, 64)
    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.1)
    st.caption(f"模型：`{MODEL}`")

    if st.button("🗑�?清空对话"):
        st.session_state.messages = []
        st.rerun()

# ── 显示历史消息 ────────────────────────────────────────────
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ── 处理用户输入 ────────────────────────────────────────────
user_input = st.chat_input("请输入你的问�?)

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Claude 思考中..."):
            # 修复：确保发送给 API 的消息列表第一条必须是 user
            # 取最�?10 条（节省 token），并过滤掉开头的 assistant 消息
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
