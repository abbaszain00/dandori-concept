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

def extract_fields(text, filename):
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

    # Extract title
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    field_labels = {"Instructor:", "Location:", "Course Type:", "Cost:"}
    title = lines[0]
    if len(lines) > 1 and lines[1] not in field_labels:
        title = title + " " + lines[1]

    instructor = get_field("Instructor", text)
    location = get_field("Location", text)
    course_type = get_field("Course Type", text)
    cost = get_field("Cost", text)

    class_id = re.search(r'Class ID:\s*([\w_]+)', text)
    class_id = class_id.group(1).strip() if class_id else ""

    # Extract file number from filename and append to class_id
    file_num_match = re.match(r'class_(\d+)_', filename)
    file_num = file_num_match.group(1) if file_num_match else "000"
    unique_id = f"{class_id}{file_num}"

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
        "unique_id": unique_id,
        "description": description,
        "skills_text": skills_text,
        "skill_keywords": ", ".join(skill_keywords)
    }

def create_database(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unique_id TEXT UNIQUE,
            title TEXT,
            instructor TEXT,
            location TEXT,
            course_type TEXT,
            cost TEXT,
            class_id TEXT,
            description TEXT,
            skills_text TEXT,
            skill_keywords TEXT
        )
    ''')
    conn.commit()

def insert_course(conn, fields):
    try:
        conn.execute('''
            INSERT OR REPLACE INTO courses 
            (unique_id, title, instructor, location, course_type, cost, class_id, description, skills_text, skill_keywords)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            fields["unique_id"],
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
        return conn.execute("SELECT changes()").fetchone()[0]
    except Exception as e:
        print(f"  ⚠️ Insert error: {e}")
        return 0

# --- Main ---
conn = sqlite3.connect(DB_PATH)
create_database(conn)

success = 0
skipped = []
failed = []

for filename in sorted(os.listdir(PDF_FOLDER)):
    if filename.endswith(".pdf"):
        path = os.path.join(PDF_FOLDER, filename)
        try:
            text = extract_text(path)
            fields = extract_fields(text, filename)

            issues = []
            if not fields["class_id"]:
                issues.append("missing class_id")
            if not fields["title"]:
                issues.append("missing title")
            if not fields["description"]:
                issues.append("missing description")

            inserted = insert_course(conn, fields)

            if inserted == 0:
                skipped.append((filename, fields["class_id"], issues or ["duplicate or ignored"]))
            else:
                success += 1
                if issues:
                    print(f"⚠️  {filename} — inserted but has issues: {', '.join(issues)}")

        except Exception as e:
            failed.append((filename, str(e)))

conn.close()

print(f"\n✅ Successfully inserted: {success}")
print(f"⏭️  Skipped (duplicate or ignored): {len(skipped)}")
for name, cid, reasons in skipped:
    print(f"   - {name} | class_id: '{cid}' | reason: {', '.join(reasons)}")
print(f"❌ Failed: {len(failed)}")
for name, err in failed:
    print(f"   - {name}: {err}")