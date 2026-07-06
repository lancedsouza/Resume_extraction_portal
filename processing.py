# import pandas as pd
# import json
# import re
# import os
# from pathlib import Path
# from langchain_community.document_loaders import PyPDFLoader
# from langchain_groq import ChatGroq
# from langgraph.graph import StateGraph, END
# from typing import TypedDict
# from dotenv import load_dotenv
# import streamlit as st

# # Load .env for local development
# load_dotenv()

# # Get API key
# api_key = os.getenv("GROQ_API_KEY")

# # If running on Streamlit Cloud, use Secrets
# if not api_key:
#     api_key = st.secrets["GROQ_API_KEY"]

# # --- LLM ---
# llm = ChatGroq(
#     model="llama-3.3-70b-versatile",
#     api_key=api_key,
#     temperature=0
# )

# # --- CONFIG ---
# EXCEL_FILE = "sample_data.xlsx"

# # --- STATE ---
# class ResumePathState(TypedDict):
#     file_path: str
#     resume_text: str
#     extracted_data: dict
#     excel_written: bool

# # --- NODES ---
# def load_pdf(state: ResumePathState) -> dict:
#     loader = PyPDFLoader(state["file_path"])
#     pages = loader.load()
#     text = "\n".join([page.page_content for page in pages])
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

# Work_experience must be an integer (total years across all roles).
# If a field is missing use empty string "".

# Resume:
# {state['resume_text']}
# """
#     response = llm.invoke(prompt)
#     raw = response.content

#     match = re.search(r'\{.*\}', raw, re.DOTALL)
#     if not match:
#         raise ValueError(f"No JSON found in LLM response: {raw}")

#     data = json.loads(match.group())

#     try:
#         data["Work_experience"] = int(str(data["Work_experience"]).strip())
#     except (ValueError, TypeError):
#         data["Work_experience"] = 0

#     return {"extracted_data": data}

# def write_to_excel(state: ResumePathState) -> dict:
#     data = state["extracted_data"]
#     excel_path = Path(EXCEL_FILE)

#     try:
#         df = pd.read_excel(excel_path)
#         current_sr_no = int(df["Sr No"].dropna().max()) + 1
#     except FileNotFoundError:
#         df = pd.DataFrame(columns=[
#             "Sr No", "Name", "Company", "Designation",
#             "Work Experience", "Location", "Contact", "Email"
#         ])
#         current_sr_no = 1

#     row1 = {
#         "Sr No": current_sr_no,
#         "Name": data["name"],
#         "Company": data["Company_1"],
#         "Designation": data["Designation_1"],
#         "Work Experience": data["Work_experience"],
#         "Location": data["Location"],
#         "Contact": data["Contact_no"],
#         "Email": data["email"]
#     }

#     row2 = {
#         "Sr No": None,
#         "Name": None,
#         "Company": data["Company_2"],
#         "Designation": data["Designation_2"],
#         "Work Experience": None,
#         "Location": None,
#         "Contact": None,
#         "Email": None
#     }

#     df = pd.concat([df, pd.DataFrame([row1, row2])], ignore_index=True)
#     df.to_excel(excel_path, index=False)
#     return {"excel_written": True}

# # --- BUILD GRAPH ---
# graph = StateGraph(ResumePathState)
# graph.add_node("load_pdf", load_pdf)
# graph.add_node("extract_data", extract_data)
# graph.add_node("write_to_excel", write_to_excel)

# graph.set_entry_point("load_pdf")
# graph.add_edge("load_pdf", "extract_data")
# graph.add_edge("extract_data", "write_to_excel")
# graph.add_edge("write_to_excel", END)

# pipeline = graph.compile()

import pandas as pd
import json
import re
import os
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from typing import TypedDict
from dotenv import load_dotenv
from tenacity import retry, wait_random_exponential, stop_after_attempt
from langchain_community.document_loaders import UnstructuredFileLoader
load_dotenv()


# --- API KEY ---
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment or .env file")

# --- LLM ---
# llm = ChatGroq(
#     model="llama-3.3-70b-versatile",
#     api_key=api_key,
#     temperature=0
# )
llm = ChatGroq(model="llama-3.1-8b-instant", api_key=api_key,temperature=0)

# --- STATE ---
class ResumePathState(TypedDict):
    file_path: str
    resume_text: str
    extracted_data: dict

# --- NODES ---
def load_pdf(state: ResumePathState) -> dict:
    # loader = PyPDFLoader(state["file_path"])
    loader = UnstructuredFileLoader(state["file_path"])
    pages = loader.load()
    text = "\n".join([page.page_content for page in pages])
    return {"resume_text": text}

@retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(5))
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

Work_experience must be an integer (total years across all roles).
If a field is missing use empty string "".

Resume:
{state['resume_text']}
"""
    response = llm.invoke(prompt)
    raw = response.content

    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in LLM response: {raw}")

    data = json.loads(match.group())

    try:
        data["Work_experience"] = int(str(data["Work_experience"]).strip())
    except (ValueError, TypeError):
        data["Work_experience"] = 0

    return {"extracted_data": data}

# --- BUILD GRAPH ---
graph = StateGraph(ResumePathState)
graph.add_node("load_pdf", load_pdf)
graph.add_node("extract_data", extract_data)

graph.set_entry_point("load_pdf")
graph.add_edge("load_pdf", "extract_data")
graph.add_edge("extract_data", END)

pipeline = graph.compile()