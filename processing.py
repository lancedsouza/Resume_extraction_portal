import json
import re
import os
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from typing import TypedDict
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found")

llm = ChatGroq(model="llama-3.1-8b-instant", api_key=api_key, temperature=0)

class ResumePathState(TypedDict):
    file_path: str
    resume_text: str
    extracted_data: dict

def load_pdf(state: ResumePathState) -> dict:
    loader = PyPDFLoader(state["file_path"])
    pages = loader.load()
    text = "\n".join([page.page_content for page in pages])
    return {"resume_text": text}

def extract_data(state: ResumePathState) -> dict:
    prompt = f"""
You are a resume parser. Extract information and return ONLY a valid JSON object.
No other text, no explanation, just the JSON.

Return exactly this structure:
{{
    "name": "candidate full name",
    "Company_1": "most recent company",
    "Designation_1": "most recent job title",
    "Company_2": "second most recent company",
    "Designation_2": "second most recent job title",
    "Work_experience": 15,
    "Location": "city",
    "Contact_no": "phone number",
    "email": "email address"
}}

Rules:
- "name" must be the actual person's full name, NOT a headline like "Accomplished Finance Professional".
  Look for the name near the contact number or email at the top of the resume.
- Work_experience must be an integer (total years across all roles).
- If a field is missing use empty string "".

Resume:
{state['resume_text']}
"""
    response = llm.invoke(prompt)
    raw = response.content
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found: {raw}")
    data = json.loads(match.group())
    try:
        data["Work_experience"] = int(str(data["Work_experience"]).strip())
    except (ValueError, TypeError):
        data["Work_experience"] = 0
    return {"extracted_data": data}

graph = StateGraph(ResumePathState)
graph.add_node("load_pdf", load_pdf)
graph.add_node("extract_data", extract_data)
graph.set_entry_point("load_pdf")
graph.add_edge("load_pdf", "extract_data")
graph.add_edge("extract_data", END)
pipeline = graph.compile()