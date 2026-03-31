import sqlite3
import json
import os
import re
import numpy as np
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

DB_PATH = "dandori.db"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

def get_all_courses():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT title, instructor, location, course_type, cost, class_id, skill_keywords, description, embedding FROM courses",
        conn
    )
    conn.close()
    return df

def get_query_embedding(query, timeout=10):
    try:
        response = client.embeddings.create(
            model="openai/text-embedding-3-small",
            input=query,
            timeout=timeout
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"  ⚠️ Embedding error: {e}")
        return None

def extract_intent(user_message, api_key):
    intent_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )
    response = intent_client.chat.completions.create(
        model="openai/gpt-4o-mini",
        temperature=0,  # keeps results consistent across runs
        messages=[{
            "role": "user",
            "content": f"""Extract the search intent from this message: "{user_message}"

Reply with JSON only, no explanation, no markdown:
{{"location": "city or region mentioned, or null", "topic": "the specific activity or subject, or null", "expanded_topic": "comma separated list of related terms to help search, or null", "specific": true or false}}

Rules:
- topic must be a specific activity or descriptive theme — never meta-words like "courses", "classes", "anything", "something", "do"
- always try to extract a meaningful topic even from indirect phrasing like "something with wood" or "I want to make things"
- expanded_topic should include synonyms, related activities, and specific examples — this helps find relevant courses
- specific should be true if the topic is a concrete well-defined activity (e.g. pottery, yoga, blacksmithing, knitting) — false if it is broad or general (e.g. food, craft, creative, fun, social)
- if topic is null, expanded_topic must also be null and specific must be false
- if no location is mentioned, location must be null

Examples:
"courses in Devon" -> {{"location": "Devon", "topic": null, "expanded_topic": null, "specific": false}}
"classes in York" -> {{"location": "York", "topic": null, "expanded_topic": null, "specific": false}}
"pottery in Brighton" -> {{"location": "Brighton", "topic": "pottery", "expanded_topic": "pottery, ceramics, clay, sculpting, wheel throwing", "specific": true}}
"anything in Devon" -> {{"location": "Devon", "topic": null, "expanded_topic": null, "specific": false}}
"something relaxing" -> {{"location": null, "topic": "relaxing", "expanded_topic": "relaxing, mindfulness, meditation, calm, zen, stress relief, gentle", "specific": false}}
"knitting classes" -> {{"location": null, "topic": "knitting", "expanded_topic": "knitting, crochet, yarn, fiber arts, wool, stitching, weaving", "specific": true}}
"hello" -> {{"location": null, "topic": null, "expanded_topic": null, "specific": false}}
"I fancy something with animals" -> {{"location": null, "topic": "animals", "expanded_topic": "animals, wildlife, creatures, hedgehog, birds, nature, foraging, ecology", "specific": false}}
"anything historical" -> {{"location": null, "topic": "historical", "expanded_topic": "historical, medieval, victorian, heritage, traditional, ancient, folklore", "specific": false}}
"something mindful" -> {{"location": null, "topic": "mindfulness", "expanded_topic": "mindfulness, meditation, zen, relaxation, wellbeing, calm, breathing", "specific": false}}
"something with wood" -> {{"location": null, "topic": "woodworking", "expanded_topic": "woodworking, carving, whittling, timber, wood crafts, joinery", "specific": true}}
"something good for stress" -> {{"location": null, "topic": "stress relief", "expanded_topic": "stress relief, relaxation, mindfulness, meditation, calm, wellbeing, gentle", "specific": false}}
"I want to make something with my hands" -> {{"location": null, "topic": "handcraft", "expanded_topic": "handcraft, making, crafting, sculpting, building, creating, hands-on", "specific": false}}
"something weird and unusual" -> {{"location": null, "topic": "unusual", "expanded_topic": "unusual, quirky, eccentric, strange, whimsical, unique, bizarre", "specific": false}}
"something to do with the sea or coast" -> {{"location": null, "topic": "coastal", "expanded_topic": "coastal, sea, ocean, beach, maritime, nautical, seaside, fishing", "specific": false}}
"something I can do with a friend" -> {{"location": null, "topic": "social activity", "expanded_topic": "social activity, group classes, team building, community, shared experiences, fun with others", "specific": false}}
"yoga in Edinburgh" -> {{"location": "Edinburgh", "topic": "yoga", "expanded_topic": "yoga, hatha yoga, vinyasa, meditation, flexibility, wellness, mindfulness", "specific": true}}
"anything with food in Cornwall" -> {{"location": "Cornwall", "topic": "food", "expanded_topic": "food, cuisine, dining, culinary experiences, local dishes, gastronomy", "specific": false}}
"something crafty in Bath" -> {{"location": "Bath", "topic": "craft", "expanded_topic": "craft, arts and crafts, DIY, handmade, creativity, workshops, making", "specific": false}}"""
        }],
        max_tokens=150
    )
    try:
        return json.loads(response.choices[0].message.content)
    except:
        return {"location": None, "topic": None, "expanded_topic": None, "specific": False}


def detect_course_reference(user_message):
    """Checks if the user is referring to a course by position (e.g. 'the second one').
    Returns a 0-based index, or None."""
    msg = user_message.lower().strip()

    ordinals = {
        "first": 0, "1st": 0,
        "second": 1, "2nd": 1,
        "third": 2, "3rd": 2,
        "fourth": 3, "4th": 3,
        "fifth": 4, "5th": 4,
        "last": -1,
    }

    for word, idx in ordinals.items():
        if re.search(rf'\b{word}\b', msg):
            return idx

    return None


def search_relevant_courses(query, df, api_key, location=None, topic=None, expanded_topic=None, specific=False, max_results=5):
    """Returns (matches, fallback) — two DataFrames. If topic search finds results,
    fallback is empty. If topic search finds nothing but the location has courses,
    those go into fallback so the user isn't left with a dead end."""
    empty = df.iloc[0:0].drop(columns=["embedding"])

    if not location and not topic:
        return empty, empty

    working_df = df.copy()

    if location:
        working_df = working_df[
            working_df["location"].str.lower().str.contains(location.lower(), na=False)
        ]
        if working_df.empty:
            return empty, empty

    # Location only, no topic — just show what's there
    if not topic:
        return working_df.drop(columns=["embedding"]).head(max_results), empty

    # Rank by topic similarity
    search_text = expanded_topic if expanded_topic else topic
    topic_embedding_raw = get_query_embedding(search_text)
    if topic_embedding_raw is None:
        return empty, empty

    topic_embedding = np.array(topic_embedding_raw)
    embeddings = np.array([json.loads(e) for e in working_df["embedding"]])
    scores = embeddings @ topic_embedding / (
        np.linalg.norm(embeddings, axis=1) * np.linalg.norm(topic_embedding)
    )
    working_df = working_df.copy()
    working_df["_score"] = scores

    if location:
        threshold = 0.47 if specific else 0.36
    else:
        threshold = 0.28

    results = working_df[working_df["_score"] >= threshold]
    results = results.sort_values("_score", ascending=False)
    results = results.drop(columns=["_score", "embedding"]).head(max_results)

    # Nothing matched the topic — fall back to showing all location courses
    if results.empty and location:
        fallback = working_df.drop(columns=["_score", "embedding"]).head(max_results)
        return empty, fallback

    return results, empty


def format_courses_for_prompt(courses_df):
    if courses_df.empty:
        return "No matching courses found."
    lines = []
    for i, (_, row) in enumerate(courses_df.iterrows(), 1):
        lines.append(
            f"{i}. {row['title']} | {row['location']} | {row['course_type']} | "
            f"{row['cost']}"
        )
    return "\n".join(lines)


def get_ai_response_stream(user_message, courses_context, api_key, chat_history=None, is_fallback=False):
    """Yields tokens one at a time for use with st.write_stream()."""
    response_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )

    system_prompt = """You are a friendly course advisor for the School of Dandori,
a UK adult wellbeing school with whimsical evening and weekend classes.

Rules:
- Only recommend courses from the list given. Never make up courses.
- Be warm and match the school's playful tone.
- Keep it brief - a couple of sentences then list suggestions.
- If no courses were found, say so honestly. Do NOT suggest alternatives from other locations or unrelated topics.
- Never pretend to be human.
- You have memory of the conversation - use it to give helpful follow up responses.
- When referring to courses, use their number from the list so the customer can refer back easily."""

    messages = [{"role": "system", "content": system_prompt}]

    if chat_history:
        for msg in chat_history[:-1]:
            messages.append({"role": msg["role"], "content": msg["content"]})

    no_results = courses_context == "No matching courses found."

    if is_fallback:
        user_prompt = f"""Customer said: "{user_message}"

I couldn't find courses matching their specific topic in this location.
However, here are ALL the courses available in their area:
{courses_context}

Tell the customer honestly that nothing matched their specific request, but show them what IS available in that area. Frame it warmly — they might spot something they fancy!"""
    elif no_results:
        user_prompt = f"""Customer said: "{user_message}"

Relevant courses found:
{courses_context}

IMPORTANT: No courses were found. Tell the customer honestly. Do NOT suggest alternatives."""
    else:
        user_prompt = f"""Customer said: "{user_message}"

Relevant courses found:
{courses_context}

Respond helpfully using the conversation history and these courses."""

    messages.append({"role": "user", "content": user_prompt})

    stream = response_client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=messages,
        max_tokens=500,
        stream=True
    )

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def get_ai_response(user_message, courses_context, api_key, chat_history=None, is_fallback=False):
    """Non-streaming wrapper — collects all tokens into a single string."""
    tokens = list(get_ai_response_stream(
        user_message, courses_context, api_key, chat_history, is_fallback
    ))
    return "".join(tokens)