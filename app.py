# School of Dandori Homepage for Searching Courses

# Import required libraries
import pandas as pd
import streamlit as st

# Configure page
st.set_page_config(
    page_title="School of Dandori",
    page_icon="🧑‍🏫",
    layout="wide"
)

# Load class data from database
def load_data():
    #data = 
    return pd.Dataframe(data)

# Load data
df = load_data()
columns = list(df.columns)
searchable_columns=["title", "instructor", "course_type","location","class_id"]

# Set columns
col_search, col_autofill, col_fields = st.column([2,2,3])

with col_search:
    query = st.text_input("Search",placeholder="Search for a course...")

with col_autofill:
    suggestions=df[[column for column in searchable_columns]].tolist()
    if query:
        suggestions = [s for s in suggestions if query.lower() in s.lower()]
    selected_name = st.selectbox("Autofill suggestion",options=[""]+suggestions,format_func=lambda x: "— select —" if x == "" else x,)

with col_fields:
    display_fields = st.multiselect("Get info about this course:",
                                    options = [c for c in columns],
                                    default=["title","location"]
                                    )

# Filter the database
active_query = selected_name if selected_name else query
if active_query:
    filtered = df[df[searchable_columns].str.contains(active_query, case=False, na=False)]
else:
    filtered = df