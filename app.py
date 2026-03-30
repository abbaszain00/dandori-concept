from dotenv import load_dotenv
import os
import re
import sqlite3
import pandas as pd
import streamlit as st

load_dotenv()

st.set_page_config(
    page_title="School of Dandori",
    page_icon="🧑‍🏫",
    layout="wide"
)

# Load courses from database
@st.cache_data
def load_data():
    conn = sqlite3.connect("dandori.db")
    df = pd.read_sql_query("SELECT * FROM courses", conn)
    conn.close()
    return df

# Strip £ sign and convert cost to float for sorting
def parse_cost(cost_str):
    if not cost_str:
        return float('inf')
    match = re.search(r'[\d.]+', cost_str)
    return float(match.group()) if match else float('inf')

df = load_data()
df = df.drop(columns=["id", "skills_text"])

# Columns we want to search across
searchable = [col for col in ["title", "instructor", "course_type", "location", "class_id", "skill_keywords"] if col in df.columns]

st.title("🌿 School of Dandori")
st.caption("Find your next wonderful class.")
st.divider()

# Search and location filter
col_search, col_location = st.columns([3, 2])

with col_search:
    query = st.text_input("Search", placeholder="🔍  keyword, location, instructor, skill...", label_visibility="hidden")

with col_location:
    locations = ["All locations"] + sorted(df["location"].dropna().unique().tolist())
    location_filter = st.selectbox("Location", locations)

# Filter by search query
if query:
    mask = df[searchable].fillna("").apply(
        lambda col: col.str.contains(query, case=False)
    ).any(axis=1)
    filtered = df[mask]
else:
    filtered = df

# Filter by location
if location_filter != "All locations":
    filtered = filtered[filtered["location"] == location_filter]

st.divider()
st.markdown(f"**{len(filtered)} course{'s' if len(filtered) != 1 else ''} found**")
st.write("")

if filtered.empty:
    st.warning("No courses found. Try a different keyword.")
else:
    # Price sorting
    sort_order = st.selectbox("Sort by price:", options=["Default", "Low to High", "High to Low"])
    if sort_order == "Low to High":
        filtered = filtered.iloc[filtered["cost"].map(parse_cost).argsort().values]
    elif sort_order == "High to Low":
        filtered = filtered.iloc[filtered["cost"].map(parse_cost).argsort()[::-1].values]

    # Display courses
    for _, row in filtered.iterrows():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"### {row['title']}")
            st.caption(f"👤 {row.get('instructor', '')}  |  📍 {row.get('location', '')}  |  🎨 {row.get('course_type', '')}")
            if pd.notna(row.get("skill_keywords")) and str(row.get("skill_keywords")).strip():
                st.caption(f"🏷️ {row['skill_keywords']}")
        with col2:
            st.metric("Cost", row.get("cost", ""))
            if st.button("Book", type="primary", key=f"{row['class_id']}_book"):
                st.write("Transferring to payment...")
        if pd.notna(row.get("description")) and str(row.get("description")).strip():
            with st.expander("Read more"):
                st.write(row["description"])
        st.write("---")