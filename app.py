import pandas as pd
import streamlit as st
import sqlite3
import re

if "booked" not in st.session_state:
    st.session_state["booked"] = 0

st.set_page_config(
    page_title="School of Dandori",
    page_icon="🧑‍🏫",
    layout="wide"
)

@st.cache_data
def load_data():
    conn = sqlite3.connect("dandori.db")
    df = pd.read_sql_query("SELECT * FROM courses", conn)
    conn.close()
    return df

df = load_data()
df_copy = df.drop(columns=["id", "skills_text"])

searchable_columns = [col for col in [
    "title", "instructor", "course_type",
    "location", "class_id", "skill_keywords"
] if col in df_copy.columns]

def parse_cost(cost_str):
    if not cost_str:
        return float('inf')
    match = re.search(r'[\d.]+', cost_str)
    return float(match.group()) if match else float('inf')

st.title("🌿 School of Dandori")
st.caption("Find your next wonderful class.")
st.divider()

col_search, col_location = st.columns([3, 2])

with col_search:
    query = st.text_input("Search a course:", placeholder="🔍  Search by keyword, location, instructor, skill...", label_visibility="hidden")

with col_location:
    locations = ["All locations"] + sorted(df_copy["location"].dropna().unique().tolist())
    location_filter = st.selectbox("Location", locations)

if query:
    mask = df_copy[searchable_columns].fillna("").apply(
        lambda col: col.str.contains(query, case=False, na=False)
    ).any(axis=1)
    filtered = df_copy[mask]
else:
    filtered = df_copy

if location_filter != "All locations":
    filtered = filtered[filtered["location"] == location_filter]

st.divider()
st.markdown(f"**{len(filtered)} course{'s' if len(filtered) != 1 else ''} found**")
st.write("")

if filtered.empty:
    st.warning("No courses found. Try a different keyword.")
else:
    sort_order = st.selectbox("Sort by Price:", options=["Default", "Price: Low to High", "Price: High to Low"])

    if sort_order == "Price: Low to High":
        filtered = filtered.iloc[filtered["cost"].map(parse_cost).argsort().values]
    elif sort_order == "Price: High to Low":
        filtered = filtered.iloc[filtered["cost"].map(parse_cost).argsort()[::-1].values]

    for _, row in filtered.iterrows():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"### {row['title']}")
            st.caption(f"👤 {row.get('instructor', '')}  |  📍 {row.get('location', '')}  |  🎨 {row.get('course_type', '')}")
            if pd.notna(row.get("skill_keywords")) and str(row.get("skill_keywords")).strip():
                st.caption(f"🏷️ {row['skill_keywords']}")
        with col2:
            st.metric("Cost", row.get("cost", ""))
            if st.button("Book this class",type="primary",key=f"{row}_book"):
                    st.session_state["booked"] = 1
                    st.write("Transferring to payment...")
        if pd.notna(row.get("description")) and str(row.get("description")).strip():
            with st.expander("Read more"):
                st.write(row["description"])
        st.write("---")