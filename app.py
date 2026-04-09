import os
import time
import random
import tempfile
import streamlit as st
from anthropic import AnthropicVertex

# ── Page config ────────────────────────────────────────────
st.set_page_config(
    page_title="Named Reactions Assistant",
    page_icon="⚗️",
    layout="wide",
)

# ── Custom CSS ─────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stChatMessage { border-radius: 12px; margin-bottom: 8px; }
    .mode-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 8px;
    }
    h1 { color: #1a1a2e; }
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# ── GCP credentials ────────────────────────────────────────
if "GOOGLE_CREDENTIALS" in st.secrets:
    creds = st.secrets["GOOGLE_CREDENTIALS"]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    tmp.write(creds.encode("utf-8"))
    tmp.close()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name

PROJECT_ID = st.secrets.get("GOOGLE_CLOUD_PROJECT", "")
REGION = st.secrets.get("GOOGLE_CLOUD_LOCATION", "us-east5")

if not PROJECT_ID:
    st.error("GOOGLE_CLOUD_PROJECT not found in Secrets.")
    st.stop()

@st.cache_resource
def get_client():
    return AnthropicVertex(project_id=PROJECT_ID, region=REGION)

try:
    client = get_client()
except Exception as e:
    st.error(f"Vertex client init failed: {e}")
    st.stop()

MODEL = "claude-haiku-4-5"

# ── Mode definitions ───────────────────────────────────────
MODES = {
    "Mechanism Explorer": {
        "icon": "🔬",
        "color": "#4361ee",
        "description": "Step-by-step reaction mechanisms",
        "system": """You are an expert organic chemistry teaching assistant specializing in named reactions.
When a user asks about a named reaction, provide:
1. A brief introduction (discoverer, year, significance)
2. The general reaction scheme (use text-based notation, e.g. R-CHO + ... → ...)
3. Step-by-step mechanism with electron pushing described clearly
4. Key conditions (reagents, solvents, temperature)
5. Substrate scope and limitations
6. 1-2 representative synthetic examples

Use clear, educational language suitable for undergraduate chemistry students.
If the user asks follow-up questions, maintain context from the conversation.
Always be precise with chemical terminology.""",
    },
    "Synthesis Advisor": {
        "icon": "🧪",
        "color": "#7209b7",
        "description": "Which reaction to use for your synthesis",
        "system": """You are a synthetic organic chemistry expert assistant.
Help the user with retrosynthetic analysis and forward synthesis planning using named reactions.
When given a target molecule or transformation, suggest appropriate named reactions and explain:
1. Why this reaction is suitable
2. Required starting materials and reagents
3. Expected yield and selectivity considerations
4. Potential competing reactions or side products
5. Alternative reactions if applicable

Think like a seasoned medicinal chemist. Be practical and concise.""",
    },
    "Quiz Mode": {
        "icon": "📝",
        "color": "#f72585",
        "description": "Test your knowledge of named reactions",
        "system": """You are an organic chemistry professor conducting a quiz on named reactions.
Your role:
- Ask one question at a time about named reactions (mechanism, conditions, substrate scope, applications)
- Vary difficulty: easy (identify the reaction), medium (predict products), hard (explain selectivity)
- After the student answers, give constructive feedback
- Award points: correct = 10pts, partially correct = 5pts, wrong = 0pts but explain the answer
- Keep a running score in your responses
- Make it engaging and educational

Start by asking your first question immediately.""",
    },
    "Reaction Finder": {
        "icon": "🔍",
        "color": "#06d6a0",
        "description": "Find reactions for a specific transformation",
        "system": """You are an expert in named reactions in organic chemistry.
Help users find the right named reaction for their needs.
When given a functional group transformation or synthetic goal:
1. List all relevant named reactions that could achieve it
2. Compare them in terms of: conditions, selectivity, availability of reagents
3. Recommend the best option with justification
4. Note any important caveats

Be comprehensive - cover classic and modern named reactions.""",
    },
}

RANDOM_PROMPTS = [
    "Tell me about the Diels-Alder reaction",
    "Explain the Grignard reaction mechanism",
    "What is the Wittig reaction used for?",
    "How does the Suzuki coupling work?",
    "Explain the Aldol condensation",
    "What is the Robinson annulation?",
    "Tell me about the Sharpless epoxidation",
    "How does the Heck reaction work?",
    "Explain the Fischer indole synthesis",
    "What is the Claisen rearrangement?",
]

# ── Session state ──────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "mode" not in st.session_state:
    st.session_state.mode = "Mechanism Explorer"
if "score" not in st.session_state:
    st.session_state.score = 0

# ── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚗️ Named Reactions")
    st.markdown("*Organic Chemistry Assistant*")
    st.divider()

    st.markdown("### Mode")
    for mode_name, mode_info in MODES.items():
        is_active = st.session_state.mode == mode_name
        if st.button(
            f"{mode_info['icon']} {mode_name}",
            key=f"btn_{mode_name}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            if st.session_state.mode != mode_name:
                st.session_state.mode = mode_name
                st.session_state.messages = []
                st.rerun()

    st.divider()
    st.markdown("### Settings")
    max_tokens = st.slider("Response length", 256, 2048, 1024, 128)
    temperature = st.slider("Creativity", 0.0, 1.0, 0.3, 0.1)

    st.divider()
    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown(f"**Model:** `{MODEL}`")
    st.markdown(f"**Region:** `{REGION}`")

# ── Main area ──────────────────────────────────────────────
current_mode = MODES[st.session_state.mode]

st.markdown(f"# {current_mode['icon']} Named Reactions Assistant")
st.markdown(f"**{st.session_state.mode}** — {current_mode['description']}")
st.divider()

# Quick start buttons
if not st.session_state.messages:
    st.markdown("#### Try asking about:")
    cols = st.columns(3)
    suggestions = random.sample(RANDOM_PROMPTS, 3)
    for i, col in enumerate(cols):
        with col:
            if st.button(suggestions[i], use_container_width=True, key=f"suggest_{i}"):
                st.session_state.messages.append({"role": "user", "content": suggestions[i]})
                st.rerun()

# ── API call with retry ────────────────────────────────────
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
            ).strip() or "No response received."
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                if attempt < retries - 1:
                    wait = 2 ** attempt
                    st.warning(f"Rate limit hit, retrying in {wait}s ({attempt+1}/{retries})...")
                    time.sleep(wait)
                    continue
                return "Rate limit exceeded (429). Please wait a moment and try again."
            return f"Error: {e}"

# ── Chat display ───────────────────────────────────────────
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ── Chat input ─────────────────────────────────────────────
placeholder = {
    "Mechanism Explorer": "Ask about any named reaction... e.g. 'Explain the Diels-Alder reaction'",
    "Synthesis Advisor": "Describe your target transformation... e.g. 'How do I make an epoxide from an alkene?'",
    "Quiz Mode": "Type your answer here...",
    "Reaction Finder": "What transformation do you need? e.g. 'aldehyde to alcohol'",
}

user_input = st.chat_input(placeholder.get(st.session_state.mode, "Ask a question..."))

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            raw = st.session_state.messages[-10:]
            while raw and raw[0]["role"] != "user":
                raw = raw[1:]
            api_messages = [{"role": m["role"], "content": m["content"]} for m in raw]
            reply = call_claude(
                api_messages,
                current_mode["system"],
                max_tokens,
                temperature,
            )
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
