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
df_copy = df.drop(columns=["id","skills_text"])
columns = list(df_copy.columns)

# include skills_text and skill_keywords in search
searchable_columns = [
    "title",
    "instructor",
    "course_type",
    "location",
    "class_id",
    "skill_keywords"
]

# make sure searchable columns exist
searchable_columns = [col for col in searchable_columns if col in df_copy.columns]

col_search, col_fields = st.columns([2, 3])

with col_search:
    query = st.text_input("Search", placeholder="Search for a course or skill keyword...")

with col_fields:
    default_fields = ["location", "skill_keywords"]
    default_fields = [f for f in default_fields if f in columns]

    display_fields = st.multiselect(
        "Get info about this course:",
        options=columns,
        default=default_fields
    )

active_query = query

if active_query:
    mask = df_copy[searchable_columns].fillna("").apply(
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
                if field in row and pd.notna(row[field]) and str(row[field]).strip():
                    # prettier labels
                    pretty_field = field.replace("_", " ").title()
                    st.markdown(f"**{pretty_field}:** {row[field]}")

            st.divider()
else:
    st.info("Search for a course above to get started.")