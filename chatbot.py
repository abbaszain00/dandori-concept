import sqlite3
import pandas as pd
from openai import OpenAI

DB_PATH = "dandori.db"

# Pull all courses from the database
def get_all_courses():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT title, instructor, location, course_type, cost, class_id, skill_keywords, description FROM courses",
        conn
    )
    conn.close()
    return df

# Simple keyword search across key fields
def search_relevant_courses(query, df, max_results=5):
    query_lower = query.lower()
    fields = ["title", "location", "course_type", "skill_keywords", "description"]
    mask = df[fields].fillna("").apply(
        lambda col: col.str.contains(query_lower, case=False)
    ).any(axis=1)
    return df[mask].head(max_results)

# Format courses into a string for the AI prompt
def format_courses_for_prompt(courses_df):
    if courses_df.empty:
        return "No matching courses found."
    lines = []
    for _, row in courses_df.iterrows():
        lines.append(
            f"- {row['title']} | {row['location']} | {row['course_type']} | "
            f"{row['cost']} | ID: {row['class_id']}"
        )
    return "\n".join(lines)

# Send user message + relevant courses to the AI and get a response
def get_ai_response(user_message, courses_context, api_key):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )

    system_prompt = """You are a friendly course advisor for the School of Dandori,
a UK adult wellbeing school with whimsical evening and weekend classes.

Rules:
- Only recommend courses from the list given. Never make up courses.
- Be warm and match the school's playful tone.
- Keep it brief - a couple of sentences then list suggestions.
- If nothing matches, say so honestly.
- Never pretend to be human."""

    user_prompt = f"""Customer said: "{user_message}"

Relevant courses:
{courses_context}

Suggest the best matches in a friendly way."""

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=500
    )
    return response.choices[0].message.content