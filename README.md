# Resume_extraction_portal
Manalot Resume Extraction Portal  An AI-powered resume parsing pipeline that extracts structured candidate data from PDF/Word resumes and exports it to Excel. Built with LangGraph, Groq LLM, and Streamlit — containerised with Docker.
# Manalot Resume Extraction Portal

An AI-powered resume parsing pipeline that extracts structured candidate data from PDF/Word resumes and exports it to Excel. Built with LangGraph, Groq LLM, and Streamlit — containerised with Docker.

---

## What It Does

1. Upload one or more resumes (PDF or Word) via the Streamlit UI
2. Each resume is passed through a LangGraph pipeline:
   - **load_pdf** → extracts raw text from the file
   - **extract_data** → sends text to Groq LLM, returns structured JSON
   - **write_to_excel** → appends candidate data to a master Excel tracker
3. Download the populated Excel file directly from the browser

---

## Project Structure

```
Resume_portal/
├── app.py               # Streamlit frontend
├── processing.py        # LangGraph pipeline (load → extract → write)
├── sample_data.xlsx     # Output Excel tracker (auto-created if missing)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Pipeline Architecture

```
START
  │
  ▼
load_pdf          → reads PDF pages, joins text into state
  │
  ▼
extract_data      → Groq LLM parses resume, returns structured JSON
  │
  ▼
write_to_excel    → appends 2 rows per candidate to Excel
  │
  ▼
END
```

Each candidate occupies **two rows** in the Excel output:
- Row 1: Sr No, Name, most recent Company + Designation, Experience, Location, Contact, Email
- Row 2: Second most recent Company + Designation only

---

## Tech Stack

| Layer | Tool |
|---|---|
| LLM | Groq `llama-3.3-70b-versatile` |
| Agent framework | LangGraph |
| PDF loading | LangChain PyPDFLoader |
| Word → PDF conversion | LibreOffice (headless) |
| Frontend | Streamlit |
| Excel output | pandas + openpyxl |
| Container | Docker + Docker Compose |

---

## Setup & Running

### Prerequisites
- Docker Desktop installed and running
- A Groq API key → [console.groq.com](https://console.groq.com)

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd Resume_portal
```

### 2. Add your Groq API key

Create a `.env` file in the root folder:

```
GROQ_API_KEY=your_api_key_here
```

### 3. Build and run

```bash
docker-compose up --build -d
```

### 4. Open the app

```
http://localhost:8501
```

### 5. Stop the app

```bash
docker-compose down
```

---

## Usage

1. Open `http://localhost:8501` in your browser
2. Upload one or more resumes (PDF, DOCX, or DOC)
3. Click **Process Resumes**
4. Review the extracted data preview on screen
5. Click **Download Master Excel** to save the populated tracker

---

## Excel Output Format

| Sr No | Name | Company | Designation | Work Experience | Location | Contact | Email |
|---|---|---|---|---|---|---|---|
| 1 | Anup Dubey | NTT Data Inc | Director | 14 | Bengaluru | +91 99999 99999 | anup@email.com |
| | | Johnson Controls | Sr. General Manager | | | | |
| 2 | Robin Gupta | ABC Corporation | Finance Lead | 15 | Mumbai | +91 88888 88888 | robin@email.com |
| | | DEF Company | Finance Manager | | | | |

---

## Troubleshooting

**Changes not reflecting after edit**
Always rebuild with `--build`:
```bash
docker-compose down
docker-compose up --build -d
```

**Check logs for errors**
```bash
docker-compose logs -f
```

**LibreOffice conversion failing**
Word → PDF conversion requires LibreOffice, which is installed in the Docker image. This will not work if you run `app.py` directly outside Docker without LibreOffice installed locally.

**Groq API errors**
- Confirm your `.env` file exists and contains a valid `GROQ_API_KEY`
- Check your Groq usage limits at [console.groq.com](https://console.groq.com)

---

## Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Your Groq API key (required) |

---

## Built By

**Manalot** — Executive Search, Mumbai  
Specialising in senior finance placements across GCCs
