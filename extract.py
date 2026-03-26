import fitz
import os
import re
import sqlite3

PDF_FOLDER = "pdfs"

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

    title = text.split('\n')[0].strip()
    instructor = get_field("Instructor", text)
    location = get_field("Location", text)
    course_type = get_field("Course Type", text)
    cost = get_field("Cost", text)
    class_id = re.search(r'Class ID:\s*([\w_]+)', text)
    class_id = class_id.group(1).strip() if class_id else ""

    desc_match = re.search(r'Course Description\s*\n(.*?)Class ID:', text, re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else ""

    return {
        "title": title,
        "instructor": instructor,
        "location": location,
        "course_type": course_type,
        "cost": cost,
        "class_id": class_id,
        "description": description
    }

# Test on one PDF first
path = "pdfs/class_140_enchanted_yarn_sculpting_crafting_mythical_creatures.pdf"
text = extract_text(path)
fields = extract_fields(text)
for k, v in fields.items():
    print(f"{k}: {v}")