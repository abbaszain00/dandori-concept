import fitz
import os
import re
import sqlite3

PDF_FOLDER = "pdfs"
DB_PATH = "dandori.db"

def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def extract_fields(text):
    def get_field(label, text):
        match = re.search(rf'{label}:\s*\n([^\n]+)', text)
        return match.group(1).strip() if match else ""

    def get_section(start_label, end_label, text):
        match = re.search(
            rf'{start_label}\s*\n(.*?){end_label}',
            text,
            re.DOTALL
        )
        return match.group(1).strip() if match else ""

    def split_lines(section_text):
        lines = []
        for line in section_text.splitlines():
            cleaned = line.strip("•- \t").strip()
            if cleaned:
                lines.append(cleaned)
        return lines

    def extract_keywords_from_skills(skills_list):
        keywords = []
        stopwords = {
            "and", "the", "with", "for", "into", "your", "their",
            "using", "develop", "developed", "understanding",
            "ability", "skills", "skill", "learn", "practice"
        }

        for skill in skills_list:
            words = re.findall(r"[A-Za-z][A-Za-z\-]+", skill.lower())
            for word in words:
                if len(word) > 2 and word not in stopwords and word not in keywords:
                    keywords.append(word)

        return keywords

    title = text.split('\n')[0].strip()
    instructor = get_field("Instructor", text)
    location = get_field("Location", text)
    course_type = get_field("Course Type", text)
    cost = get_field("Cost", text)

    class_id = re.search(r'Class ID:\s*([\w_]+)', text)
    class_id = class_id.group(1).strip() if class_id else ""

    desc_match = re.search(r'Course Description\s*\n(.*?)Class ID:', text, re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else ""

    skills_text = get_section("Skills Developed", "Course Description", text)
    skills_list = split_lines(skills_text)
    skill_keywords = extract_keywords_from_skills(skills_list)

    return {
        "title": title,
        "instructor": instructor,
        "location": location,
        "course_type": course_type,
        "cost": cost,
        "class_id": class_id,
        "description": description,
        "skills_text": skills_text,
        "skill_keywords": ", ".join(skill_keywords)
    }

def create_database(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            instructor TEXT,
            location TEXT,
            course_type TEXT,
            cost TEXT,
            class_id TEXT UNIQUE,
            description TEXT,
            skills_text TEXT,
            skill_keywords TEXT
        )
    ''')
    conn.commit()

def insert_course(conn, fields):
    conn.execute('''
        INSERT OR IGNORE INTO courses 
        (title, instructor, location, course_type, cost, class_id, description, skills_text, skill_keywords)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        fields["title"],
        fields["instructor"],
        fields["location"],
        fields["course_type"],
        fields["cost"],
        fields["class_id"],
        fields["description"],
        fields["skills_text"],
        fields["skill_keywords"]
    ))
    conn.commit()

# --- Main ---
conn = sqlite3.connect(DB_PATH)
create_database(conn)

success = 0
failed = []

for filename in os.listdir(PDF_FOLDER):
    if filename.endswith(".pdf"):
        path = os.path.join(PDF_FOLDER, filename)
        try:
            text = extract_text(path)
            fields = extract_fields(text)
            insert_course(conn, fields)
            success += 1

            print(f"\nProcessed: {filename}")
            print("Title:", fields["title"])
            print("Skill keywords:", fields["skill_keywords"])

        except Exception as e:
            failed.append((filename, str(e)))

conn.close()

print(f"\nSuccessfully extracted: {success}")
print(f"Failed: {len(failed)}")
if failed:
    for name, err in failed:
        print(f"  - {name}: {err}")