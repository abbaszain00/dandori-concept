import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from dotenv import load_dotenv
from chatbot import get_all_courses, search_relevant_courses, format_courses_for_prompt, get_ai_response

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

st.title("🌿 Course Discovery")
st.caption("Tell us what you're looking for and we'll find something wonderful.")
st.divider()

# Keep chat history across reruns
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle new message
if prompt := st.chat_input("e.g. something creative in Devon, or a relaxing class this weekend..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Finding something wonderful..."):
            df = get_all_courses()
            matches = search_relevant_courses(prompt, df)
            context = format_courses_for_prompt(matches)
            reply = get_ai_response(prompt, context, api_key)
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})