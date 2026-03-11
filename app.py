import os
import streamlit as st
from google import genai

client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY")
)

st.title("Claude Chat")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

user_input = st.chat_input("Ask something")

if user_input:
    st.session_state.messages.append({"role":"user","content":user_input})

    with st.chat_message("assistant"):
        response = client.models.generate_content(
            model="claude-sonnet-4-5@20250929",
            contents=user_input
        )

        reply = response.text
        st.markdown(reply)

    st.session_state.messages.append({"role":"assistant","content":reply})