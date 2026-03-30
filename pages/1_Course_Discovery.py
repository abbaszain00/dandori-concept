import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from chatbot import get_all_courses, extract_intent, search_relevant_courses, format_courses_for_prompt, get_ai_response

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

st.title("🌿 Course Discovery")
st.caption("Tell us what you're looking for and we'll find something wonderful.")
st.divider()

# Keep chat history and last known intent across reruns
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_location" not in st.session_state:
    st.session_state.last_location = None
if "last_topic" not in st.session_state:
    st.session_state.last_topic = None

def render_course_card(row, msg_index):
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"### {row['title']}")
        st.caption(f"👤 {row.get('instructor', '')}  |  📍 {row.get('location', '')}  |  🎨 {row.get('course_type', '')}")
        if pd.notna(row.get("skill_keywords")) and str(row.get("skill_keywords")).strip():
            st.caption(f"🏷️ {row['skill_keywords']}")
    with col2:
        st.metric("Cost", row.get("cost", ""))
        if st.button("Book", type="primary", key=f"chat_{msg_index}_{row['class_id']}_book"):
            st.write("Transferring to payment...")
    if pd.notna(row.get("description")) and str(row.get("description")).strip():
        with st.expander("Read more"):
            st.write(row["description"])
    st.write("---")

# Show previous messages and their course cards
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "courses" in msg and not msg["courses"].empty:
            st.divider()
            for _, row in msg["courses"].iterrows():
                render_course_card(row, i)

# Handle new message
if prompt := st.chat_input("e.g. something creative in Devon, or a relaxing class this weekend..."):
    
    # Reset context if user wants to start fresh
    reset_phrases = ["forget that", "never mind", "start over", "ignore that", "actually forget"]
    if any(phrase in prompt.lower() for phrase in reset_phrases):
        st.session_state.last_location = None
        st.session_state.last_topic = None
        st.session_state.last_expanded_topic = None

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Finding something wonderful..."):
            df = get_all_courses()

            # Extract intent from current message
            intent = extract_intent(prompt, api_key)
new_location = intent.get("location")
new_topic = intent.get("topic")
new_expanded_topic = intent.get("expanded_topic")
new_specific = intent.get("specific", False)

location = new_location if new_location else st.session_state.last_location
topic = new_topic if new_topic else last_topic
expanded_topic = new_expanded_topic if new_expanded_topic else st.session_state.get("last_expanded_topic")
specific = new_specific

if not new_location and not new_topic:
    location = None
    topic = None
    expanded_topic = None
    specific = False
    st.session_state.last_location = None
    st.session_state.last_topic = None
    st.session_state.last_expanded_topic = None
else:
    if new_location:
        st.session_state.last_location = new_location
    if new_topic:
        st.session_state.last_topic = new_topic
    if new_expanded_topic:
        st.session_state.last_expanded_topic = new_expanded_topic

matches = search_relevant_courses(
    prompt, df, api_key,
    location=location,
    topic=topic,
    expanded_topic=expanded_topic,
    specific=specific
)
            context = format_courses_for_prompt(matches)
            reply = get_ai_response(prompt, context, api_key, chat_history=st.session_state.messages)
            st.markdown(reply)

            if not matches.empty:
                st.divider()
                for _, row in matches.iterrows():
                    render_course_card(row, len(st.session_state.messages))

    st.session_state.messages.append({
        "role": "assistant",
        "content": reply,
        "courses": matches
    })