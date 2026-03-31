# School of Dandori — Course Discovery Platform

The School of Dandori runs whimsical evening and weekend classes for adults across the UK. Before this project, every course lived in its own PDF file and finding anything meant opening files by hand. Customers had no way to browse or search online.

This project gives the school a searchable course catalogue and a natural language discovery interface so customers can describe what they want and get relevant suggestions back.

---

## Phase 1 — Course Catalogue

All 211 course PDFs are extracted into a SQLite database. From there, customers can search by keyword, filter by location, sort by price, and book directly through the site.

## Phase 2 — Course Discovery

A conversational interface where customers can say things like "something relaxing in Devon" or "anything with food in Cornwall" and get real suggestions back. It understands follow-up questions, remembers what was discussed earlier in the conversation, and only ever recommends courses from the school's own catalogue.

---

## Running locally

You'll need an `OPENROUTER_API_KEY` in a `.env` file.

```bash
pip install -r requirements.txt
python extract.py        # builds the database (~5 mins)
streamlit run app.py     # runs the app at localhost:8501
```

## Docker

```bash
docker build --build-arg OPENROUTER_API_KEY=your_key_here -t dandori .
docker run -p 8080:8080 dandori
```

---

## Project structure

```
dandori-concept/
├── app.py                        # Catalogue page
├── chatbot.py                    # Discovery logic
├── extract.py                    # PDF extraction
├── pages/
│   ├── 1_Course_Discovery.py     # Conversational UI
│   └── payment.py                # Booking form
├── assets/
│   └── style.css
├── pdfs/                         # Course PDFs (gitignored)
├── dandori.db                    # SQLite database (gitignored)
├── requirements.txt
└── Dockerfile
```

---

## Contributors

Abbas Zain, Marco, Elora — Digital Futures Frontier AI programme, 2026.
