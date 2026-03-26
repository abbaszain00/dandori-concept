import pandas as pd
import streamlit as st
import sqlite3

st.set_page_config(
    page_title="School of Dandori",
    page_icon="🧑‍🏫",
    layout="wide"
)

def load_data():
    conn = sqlite3.connect("dandori.db")
    df = pd.read_sql_query("SELECT * FROM courses", conn)
    conn.close()
    return df

df = load_data()
columns = list(df.columns)
searchable_columns = ["title", "instructor", "course_type", "location", "class_id"]

col_search, col_autofill, col_fields = st.columns([2, 2, 3])

with col_search:
    query = st.text_input("Search", placeholder="Search for a course...")

with col_autofill:
    suggestions = pd.unique(df[searchable_columns].values.ravel())
    suggestions = [str(s) for s in suggestions if isinstance(s, str)]
    if query:
        suggestions = [s for s in suggestions if query.lower() in s.lower()]
    selected_name = st.selectbox(
        "Autofill suggestion",
        options=[""] + suggestions,
        format_func=lambda x: "— select —" if x == "" else x
    )

with col_fields:
    display_fields = st.multiselect(
        "Get info about this course:",
        options=[c for c in columns],
        default=["title", "location"]
    )

active_query = selected_name if selected_name else query
if active_query:
    mask = df[searchable_columns].apply(
        lambda col: col.str.contains(active_query, case=False, na=False)
    ).any(axis=1)
    filtered = df[mask]
else:
    filtered = df

st.divider()

if active_query:
    st.markdown(f"**{len(filtered)} course{'s' if len(filtered) != 1 else ''} found**")
    if filtered.empty:
        st.warning("No courses found.")
    else:
        for _, row in filtered.iterrows():
            st.markdown(f"### {row['title']}")
            for field in display_fields:
                if field in row:
                    st.markdown(f"**{field}:** {row[field]}")
            st.divider()
else:
    st.info("Search for a course above to get started.")