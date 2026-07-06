# import json
# import re
# import os
# import time
# import mammoth
# import pdfplumber
# from pathlib import Path
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langgraph.graph import StateGraph, END
# from typing import TypedDict
# from dotenv import load_dotenv

# load_dotenv()

# gemini_key = os.getenv("GEMINI_API_KEY")
# if not gemini_key:
#     raise ValueError("GEMINI_API_KEY not found")

# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.0-flash",
#     google_api_key=gemini_key,
#     temperature=0
# )

# class ResumePathState(TypedDict):
#     file_path: str
#     resume_text: str
#     extracted_data: dict

# def load_file(state: ResumePathState) -> dict:
#     path = Path(state["file_path"])

#     if path.suffix.lower() == ".pdf":
#         text_parts = []
#         with pdfplumber.open(str(path)) as pdf:
#             for page in pdf.pages:
#                 text = page.extract_text(layout=True)
#                 if text:
#                     text_parts.append(text)
#         text = "\n".join(text_parts)

#     elif path.suffix.lower() in [".docx", ".doc"]:
#         with open(str(path), "rb") as f:
#             result = mammoth.extract_raw_text(f)
#             text = result.value

#     else:
#         raise ValueError(f"Unsupported file type: {path.suffix}")

#     if not text.strip():
#         raise ValueError(f"No text extracted from {path.name}")

#     return {"resume_text": text}

# def extract_data(state: ResumePathState) -> dict:
#     prompt = f"""
# You are a resume parser. Extract information and return ONLY a valid JSON object.
# No other text, no explanation, just the JSON.

# Return exactly this structure:
# {{
#     "name": "candidate full name",
#     "Company_1": "most recent company",
#     "Designation_1": "most recent job title",
#     "Company_2": "second most recent company",
#     "Designation_2": "second most recent job title",
#     "Work_experience": 15,
#     "Location": "city",
#     "Contact_no": "phone number",
#     "email": "email address"
# }}

# Rules:
# - "name" must be the actual person's full name e.g. "Nirzara Awati".
#   NOT a headline like "HR Manager". Look near the top of the resume,
#   close to email and phone number.
# - Work_experience must be an integer (total years across all roles).
# - If a field is missing use empty string "".

# Resume:
# {state['resume_text']}
# """
#     for attempt in range(3):
#         try:
#             response = llm.invoke(prompt)
#             raw = response.content
#             match = re.search(r'\{.*\}', raw, re.DOTALL)
#             if not match:
#                 raise ValueError(f"No JSON found: {raw}")
#             data = json.loads(match.group())
#             try:
#                 data["Work_experience"] = int(str(data["Work_experience"]).strip())
#             except (ValueError, TypeError):
#                 data["Work_experience"] = 0
#             return {"extracted_data": data}

#         except Exception as e:
#             if "429" in str(e) or "quota" in str(e).lower():
#                 time.sleep((attempt + 1) * 10)
#                 continue
#             raise

#     raise RuntimeError("Failed after 3 retries")

# # --- GRAPH ---
# graph = StateGraph(ResumePathState)
# graph.add_node("load_file", load_file)
# graph.add_node("extract_data", extract_data)
# graph.set_entry_point("load_file")
# graph.add_edge("load_file", "extract_data")
# graph.add_edge("extract_data", END)
# pipeline = graph.compile()
import json, re, os, mammoth, pdfplumber, pandas as pd
from pathlib import Path
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from typing import TypedDict

# Fast LLM for extraction
llm = ChatGroq(model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))

class ResumePathState(TypedDict):
    file_path: str
    extracted_data: dict

def load_and_extract(state: ResumePathState) -> dict:
    path = Path(state["file_path"])
    # Extraction logic
    if path.suffix.lower() == ".pdf":
        with pdfplumber.open(str(path)) as pdf:
            text = "\n".join([p.extract_text() or "" for p in pdf.pages])
    else:
        with open(str(path), "rb") as f:
            text = mammoth.extract_raw_text(f).value
            
    # LLM Parsing
    prompt = f"Extract resume info to JSON: {text}"
    response = llm.invoke(prompt).content
    match = re.search(r'\{.*\}', response, re.DOTALL)
    data = json.loads(match.group()) if match else {}
    
    # Save to Excel (The Worker's job!)
    excel_path = Path("/app/data/master_resume_data.xlsx")
    new_data = pd.DataFrame([data])
    if excel_path.exists():
        df = pd.concat([pd.read_excel(excel_path), new_data], ignore_index=True)
    else:
        df = new_data
    df.to_excel(excel_path, index=False)
    
    return {"extracted_data": data}

builder = StateGraph(ResumePathState)
builder.add_node("process", load_and_extract)
builder.set_entry_point("process")
builder.add_edge("process", END)
pipeline = builder.compile()

def pipeline_wrapper(file_path):
    return pipeline.invoke({"file_path": file_path})