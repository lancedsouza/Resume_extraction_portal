# import json, re, os, mammoth, pdfplumber, pandas as pd
# from pathlib import Path
# from langchain_groq import ChatGroq
# from langgraph.graph import StateGraph, END
# from typing import TypedDict

# # Initialize Groq LLM
# llm = ChatGroq(model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))

# class ResumePathState(TypedDict):
#     file_path: str
#     extracted_data: dict

# def load_and_extract(state: ResumePathState) -> dict:
#     path = Path(state["file_path"])
#     text = ""
    
#     # PDF Extraction
#     if path.suffix.lower() == ".pdf":
#         with pdfplumber.open(str(path)) as pdf:
#             # Using list comprehension to safely extract text
#             text = "\n".join([page.extract_text() or "" for page in pdf.pages])
            
#     # DOCX/DOC Extraction
#     elif path.suffix.lower() in [".docx", ".doc"]:
#         with open(str(path), "rb") as f:
#             # Mammoth.extract_raw_text returns an object with a .value attribute
#             result = mammoth.extract_raw_text(f)
#             text = result.value
            
#     # AI Extraction
#     MAX_CHARS = 15000 
#     truncated_text = text[:MAX_CHARS]
    
#     prompt = f"Extract resume info to JSON: {truncated_text}"
#     response = llm.invoke(prompt).content
#     match = re.search(r'\{.*\}', response, re.DOTALL)
#     data = json.loads(match.group()) if match else {}
    
#     return {"extracted_data": data}

# def save_to_excel(state: ResumePathState) -> dict:
#     # Use relative path 'data/'
#     data_dir = Path("data")
#     data_dir.mkdir(exist_ok=True)
#     excel_path = data_dir / "master_resume_data.xlsx"
    
#     new_data = pd.DataFrame([state["extracted_data"]])
    
#     if excel_path.exists():
#         df = pd.read_excel(excel_path)
#         df = pd.concat([df, new_data], ignore_index=True)
#     else:
#         df = new_data
        
#     df.to_excel(excel_path, index=False)
#     return {"extracted_data": state["extracted_data"]}

# # Define the graph
# builder = StateGraph(ResumePathState)
# builder.add_node("extract", load_and_extract)
# builder.add_node("save", save_to_excel)
# builder.set_entry_point("extract")
# builder.add_edge("extract", "save")
# builder.add_edge("save", END)
# pipeline = builder.compile()

# def pipeline_wrapper(file_path):
#     return pipeline.invoke({"file_path": file_path})
# Code from claude
# import json, re, os, mammoth, pdfplumber, time
# from pathlib import Path
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langgraph.graph import StateGraph, END
# from typing import TypedDict
# from pypdf import PdfReader

# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.0-flash-lite",  # ← faster
#     google_api_key=os.getenv("GEMINI_API_KEY"),
#     temperature=0
# )
# class ResumePathState(TypedDict):
#     file_path: str
#     extracted_data: dict

# def load_and_extract(state: ResumePathState) -> dict:
#     path = Path(state["file_path"])
#     text = ""

#     if path.suffix.lower() == ".pdf":
#        reader = PdfReader(str(path))
#        text = "\n".join([page.extract_text() or "" for page in reader.pages])

#     elif path.suffix.lower() in [".docx", ".doc"]:
#         with open(str(path), "rb") as f:
#             text = mammoth.extract_raw_text(f).value

#     if not text.strip():
#         raise ValueError(f"No text extracted from {path.name}")

#     prompt = f"""
# You are a resume parser. Return ONLY a valid JSON object. No markdown, no explanation.

# Return exactly this flat structure with no nested objects:
# {{
#     "name": "candidate full name",
#     "Company_1": "most recent company name only",
#     "Designation_1": "most recent job title only",
#     "Company_2": "second most recent company name only",
#     "Designation_2": "second most recent job title only",
#     "Work_experience": 10,
#     "Location": "city name only",
#     "Contact_no": "phone number only",
#     "email": "email address only"
# }}

# Critical rules:
# - Return ONLY the JSON object, nothing else
# - All values must be plain strings or integers — no nested objects or arrays
# - "name" is the person's actual full name, NOT a job title
# - Work_experience is total years as a single integer
# - If a field is missing use empty string ""

# Resume:
# {text[:5000]}  # was 10000
# """
#     for attempt in range(3):
#         try:
#             response = llm.invoke(prompt).content
#             # Strip markdown code blocks if present
#             response = re.sub(r'```json|```', '', response).strip()
#             match = re.search(r'\{.*\}', response, re.DOTALL)
#             if not match:
#                 raise ValueError(f"No JSON found: {response}")
#             data = json.loads(match.group())

#             # Force all values to be flat strings/ints
#             flat = {
#                 "name": str(data.get("name", "")),
#                 "Company_1": str(data.get("Company_1", "")),
#                 "Designation_1": str(data.get("Designation_1", "")),
#                 "Company_2": str(data.get("Company_2", "")),
#                 "Designation_2": str(data.get("Designation_2", "")),
#                 "Work_experience": 0,
#                 "Location": str(data.get("Location", "")),
#                 "Contact_no": str(data.get("Contact_no", "")),
#                 "email": str(data.get("email", ""))
#             }
#             try:
#                 flat["Work_experience"] = int(str(data.get("Work_experience", 0)).strip())
#             except (ValueError, TypeError):
#                 flat["Work_experience"] = 0

#             return {"extracted_data": flat}

#         except Exception as e:
#             if "429" in str(e) or "quota" in str(e).lower():
#                 time.sleep((attempt + 1) * 10)
#                 continue
#             raise

#     raise RuntimeError("Failed after 3 retries")

# # --- GRAPH ---
# builder = StateGraph(ResumePathState)
# builder.add_node("extract", load_and_extract)
# builder.set_entry_point("extract")
# builder.add_edge("extract", END)
# pipeline = builder.compile()

# def pipeline_wrapper(file_path: str):
#     return pipeline.invoke({"file_path": file_path})

# Code from Qwen
import json, re, os, mammoth, pdfplumber, pandas as pd
from pathlib import Path
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from typing import TypedDict

# Initialize Groq LLM
llm = ChatGroq(model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))

class ResumePathState(TypedDict):
    file_path: str
    extracted_data: dict

import streamlit as st
import pandas as pd
from pathlib import Path
import os
import shutil
import time 
from processing import pipeline

# Configure Page
st.set_page_config(page_title="Manalot | AI Resume Scout", layout="wide")
st.title("📄 Manalot AI Resume Scout")

# 1. FIX: Use a local folder instead of /app/data
# Use a relative path! This creates a folder inside your app's directory.
DATA_DIR = Path("data") 
DATA_DIR.mkdir(exist_ok=True)

# Initialize Session State
if 'results' not in st.session_state:
    st.session_state.results = []

uploaded_files = st.file_uploader("Upload Resumes", accept_multiple_files=True, type=['pdf', 'docx', 'doc'])

if st.button("🚀 Start Extraction"):
    if not uploaded_files:
        st.warning("Please upload files first.")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, file in enumerate(uploaded_files):
            status_text.text(f"Analyzing {file.name}...")
            
            # Save file to local 'data/' folder
            temp_path = DATA_DIR / file.name
            with open(temp_path, "wb") as f:
                f.write(file.getbuffer())
            
            # --- RETRY LOGIC WITH EXPONENTIAL BACKOFF ---
            max_retries = 4
            processed = False
            
            for attempt in range(max_retries):
                try:
                    # Run Pipeline
                    res = pipeline.invoke({"file_path": str(temp_path)})
                    st.session_state.results.append(res["extracted_data"])
                    processed = True
                    break # Success, exit the retry loop
                except Exception as e:
                    error_msg = str(e)
                    # Check if the error is specifically a rate limit (429)
                    if "rate_limit_exceeded" in error_msg or "429" in error_msg:
                        # Wait 5s, then 10s, then 20s, then 40s
                        wait_time = 5 * (2 ** attempt) 
                        st.warning(f"⏳ Rate limit hit for {file.name}. Waiting {wait_time}s and retrying ({attempt+1}/{max_retries})...")
                        time.sleep(wait_time)
                    else:
                        st.error(f"Failed to process {file.name}: {e}")
                        break # If it's a different error, stop retrying
            
            if not processed:
                st.error(f"Skipped {file.name} after {max_retries} retries.")
            # ------------------------------------------
            
            # Cleanup temp file
            if temp_path.exists():
                os.remove(temp_path)
            
            # ADD A SMALL DELAY BETWEEN FILES
            # This spaces out your requests so you don't hit the 6000 TPM limit as quickly
            time.sleep(1.5) 
            
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        status_text.text("Extraction Complete!")

# --- DISPLAY RESULTS (FIXED FOR PYARROW CRASH) ---
if st.session_state.results:
    df = pd.DataFrame(st.session_state.results)
    
    # FIX: Convert all columns to strings to prevent PyArrow crashes 
    # when the LLM returns nested JSON (lists/dicts) in the dataframe
    df_display = df.astype(str)
    
    st.dataframe(df_display, use_container_width=True)
    
    # For the CSV download, we use the original df so Excel/CSV parsers 
    # can still attempt to read the raw data if needed
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download CSV", csv, "results.csv", "text/csv")

def save_to_excel(state: ResumePathState) -> dict:
    # Use relative path 'data/'
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    excel_path = data_dir / "master_resume_data.xlsx"
    
    new_data = pd.DataFrame([state["extracted_data"]])
    
    if excel_path.exists():
        df = pd.read_excel(excel_path)
        df = pd.concat([df, new_data], ignore_index=True)
    else:
        df = new_data
        
    df.to_excel(excel_path, index=False)
    return {"extracted_data": state["extracted_data"]}

# Define the graph
builder = StateGraph(ResumePathState)
builder.add_node("extract", load_and_extract)
builder.add_node("save", save_to_excel)
builder.set_entry_point("extract")
builder.add_edge("extract", "save")
builder.add_edge("save", END)
pipeline = builder.compile()

def pipeline_wrapper(file_path):
    return pipeline.invoke({"file_path": file_path})