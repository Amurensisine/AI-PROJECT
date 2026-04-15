import random
import streamlit as st
from google import genai
from google.genai import types

# ── Page config ────────────────────────────────────────────
st.set_page_config(
    page_title="Named Reactions Assistant",
    page_icon="⚗️",
    layout="wide",
)

st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stChatMessage { border-radius: 12px; margin-bottom: 8px; }
    h1 { color: #1a1a2e; }
    .stButton > button { border-radius: 8px; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# ── Gemini API setup ───────────────────────────────────────
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY not found in Secrets.")
    st.stop()

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash"

# ── Mode definitions ───────────────────────────────────────
MODES = {
    "Mechanism Explorer": {
        "icon": "🔬",
        "description": "Step-by-step reaction mechanisms",
        "system": """You are an expert organic chemistry teaching assistant specializing in named reactions.
When a user asks about a named reaction, provide:
1. A brief introduction (discoverer, year, significance)
2. The general reaction scheme (use text-based notation, e.g. R-CHO + ... -> ...)
3. Step-by-step mechanism with electron pushing described clearly
4. Key conditions (reagents, solvents, temperature)
5. Substrate scope and limitations
6. 1-2 representative synthetic examples

Use clear, educational language suitable for undergraduate chemistry students.
Always be precise with chemical terminology.""",
    },
    "Synthesis Advisor": {
        "icon": "🧪",
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
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None

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
    st.markdown(f"**Model:** `{MODEL_NAME}`")

# ── Main area ──────────────────────────────────────────────
current_mode = MODES[st.session_state.mode]

st.markdown(f"# {current_mode['icon']} Named Reactions Assistant")
st.markdown(f"**{st.session_state.mode}** — {current_mode['description']}")
st.divider()

if not st.session_state.messages and st.session_state.pending_input is None:
    st.markdown("#### Try asking about:")
    cols = st.columns(3)
    suggestions = random.sample(RANDOM_PROMPTS, 3)
    for i, col in enumerate(cols):
        with col:
            if st.button(suggestions[i], use_container_width=True, key=f"suggest_{i}"):
                st.session_state.pending_input = suggestions[i]
                st.rerun()

# ── API call ───────────────────────────────────────────────
def call_gemini(messages, system_prompt, max_tokens, temperature):
    try:
        history = []
        for msg in messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            history.append(types.Content(
                role=role,
                parts=[types.Part(text=msg["content"])]
            ))

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=history + [types.Content(
                role="user",
                parts=[types.Part(text=messages[-1]["content"])]
            )],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=max_tokens,
                temperature=temperature,
            )
        )
        return response.text
    except Exception as e:
        return f"Error: {e}"

# ── Chat display ───────────────────────────────────────────
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ── Chat input ─────────────────────────────────────────────
placeholder = {
    "Mechanism Explorer": "Ask about any named reaction... e.g. 'Explain the Diels-Alder reaction'",
    "Synthesis Advisor": "Describe your target transformation...",
    "Quiz Mode": "Type your answer here...",
    "Reaction Finder": "What transformation do you need? e.g. 'aldehyde to alcohol'",
}

user_input = st.chat_input(placeholder.get(st.session_state.mode, "Ask a question..."))

# Handle suggestion button clicks
if st.session_state.pending_input is not None:
    user_input = st.session_state.pending_input
    st.session_state.pending_input = None

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = call_gemini(
                st.session_state.messages,
                current_mode["system"],
                max_tokens,
                temperature,
            )
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
