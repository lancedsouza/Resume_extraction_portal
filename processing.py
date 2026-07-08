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
#             text = "\n".join([page.extract_text() or "" for page in pdf.pages])
            
#     # DOCX/DOC Extraction
#     elif path.suffix.lower() in [".docx", ".doc"]:
#         with open(str(path), "rb") as f:
#             result = mammoth.extract_raw_text(f)
#             text = result.value
            
#     # AI Extraction
#     MAX_CHARS = 5000 
#     truncated_text = text[:MAX_CHARS]
    
#     # Prompt engineered to return flat JSON to prevent PyArrow crashes later
#     prompt = f"""
#     Extract resume information and return ONLY a valid, flat JSON object. 
#     Do not use nested arrays or objects. If a candidate has multiple jobs or degrees, 
#     combine them into a single string separated by semicolons (;).
    
#     Resume text: 
#     {truncated_text}
#     """
    
#     response = llm.invoke(prompt).content
#     match = re.search(r'\{.*\}', response, re.DOTALL)
    
#     # Safety check in case LLM returns invalid JSON
#     try:
#         data = json.loads(match.group()) if match else {}
#     except json.JSONDecodeError:
#         data = {"error": "Failed to parse LLM JSON response"}
    
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

# # Compile the pipeline
# pipeline = builder.compile()

# # NOTE: DO NOT put "from processing import pipeline" at the bottom of this file!

# # code from Gemini
# import os, json, re, mammoth, pdfplumber, time
# from pathlib import Path
# from langchain_groq import ChatGroq
# from langgraph.graph import StateGraph, END
# from typing import TypedDict

# llm = ChatGroq(model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))

# class ResumePathState(TypedDict):
#     file_path: str
#     extracted_data: dict

# def load_and_extract(state: ResumePathState) -> dict:
#     path = Path(state["file_path"])
#     text = ""
#     if path.suffix.lower() == ".pdf":
#         with pdfplumber.open(str(path)) as pdf:
#             text = "\n".join([p.extract_text() or "" for p in pdf.pages])
#     elif path.suffix.lower() in [".docx", ".doc"]:
#         with open(str(path), "rb") as f:
#             text = mammoth.extract_raw_text(f).value
            
#     prompt = f"""
#     Extract resume details. Return ONLY pure JSON.
#     Location must be the City only. 
#     Capture the 2 most recent roles:
#     1. 'recent_company', 'recent_designation'
#     2. 'previous_company', 'previous_designation'
    
#     JSON Schema:
#     {{
#         "name": "Full Name",
#         "email": "Email",
#         "location": "City only",
#         "total_experience": "Exact string",
#         "recent_company": "str",
#         "recent_designation": "str",
#         "previous_company": "str",
#         "previous_designation": "str"
#     }}
#     Text: {text[:10000]}
#     """
    
#     response = llm.invoke(prompt).content
#     json_str = re.sub(r'[\s\S]*?(\{[\s\S]*\})[\s\S]*', r'\1', response)
#     try:
#         return {"extracted_data": json.loads(json_str)}
#     except:
#         return {"extracted_data": {"error": "JSON Parse Error"}}

# builder = StateGraph(ResumePathState)
# builder.add_node("extract", load_and_extract)
# builder.set_entry_point("extract")
# builder.add_edge("extract", END)
# pipeline = builder.compile()

# def pipeline_wrapper(file_path):
#     return pipeline.invoke({"file_path": file_path})
# # code from Gemini matched to Anil's excel
# import os, json, re, mammoth, pdfplumber
# from pathlib import Path
# from langchain_groq import ChatGroq
# from langgraph.graph import StateGraph, END
# from typing import TypedDict

# llm = ChatGroq(model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))

# class ResumePathState(TypedDict):
#     file_path: str
#     extracted_data: dict

# def load_and_extract(state: ResumePathState) -> dict:
#     path = Path(state["file_path"])
#     text = ""
#     if path.suffix.lower() == ".pdf":
#         with pdfplumber.open(str(path)) as pdf:
#             text = "\n".join([p.extract_text() or "" for p in pdf.pages])
#     elif path.suffix.lower() in [".docx", ".doc"]:
#         with open(str(path), "rb") as f:
#             text = mammoth.extract_raw_text(f).value
            
#     prompt = f"""
#     Extract resume details into STRICT JSON. 
#     Location: City only.
#     Experience: Total years.
#     2 most recent roles: 'recent_company', 'recent_designation', 'prev_company', 'prev_designation'.
    
#     JSON Schema:
#     {{"name": "Name", "email": "Email", "location": "City", "total_exp": "Years", "recent_company": "Comp", "recent_designation": "Desig", "prev_company": "Comp", "prev_designation": "Desig"}}
#     Text: {text[:10000]}
#     """
    
#     response = llm.invoke(prompt).content
#     json_str = re.sub(r'[\s\S]*?(\{[\s\S]*\})[\s\S]*', r'\1', response)
#     try:
#         return {"extracted_data": json.loads(json_str)}
#     except:
#         return {"extracted_data": {"error": "JSON Parse Error"}}

# builder = StateGraph(ResumePathState)
# builder.add_node("extract", load_and_extract)
# builder.set_entry_point("extract")
# builder.add_edge("extract", END)
# pipeline = builder.compile()

# def pipeline_wrapper(file_path):
#     return pipeline.invoke({"file_path": file_path})

# Processing .py with gemini increase token limit
# import os, json, re, mammoth, pdfplumber, time
# from pathlib import Path
# from langchain_groq import ChatGroq
# from langgraph.graph import StateGraph, END
# from typing import TypedDict

# # Initialize Groq
# llm = ChatGroq(model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))

# class ResumePathState(TypedDict):
#     file_path: str
#     extracted_data: dict

# def invoke_with_retry(prompt, retries=5):
#     """Exponential backoff: waits longer if Groq hits us with a Rate Limit."""
#     for i in range(retries):
#         try:
#             return llm.invoke(prompt)
#         except Exception as e:
#             if "429" in str(e):
#                 sleep_time = 10 * (2 ** i) 
#                 time.sleep(sleep_time)
#             else:
#                 raise e
#     return llm.invoke(prompt)

# def load_and_extract(state: ResumePathState) -> dict:
#     path = Path(state["file_path"])
#     text = ""
    
#     # NEW: Trying a more aggressive text extraction
#     try:
#         if path.suffix.lower() == ".pdf":
#             with pdfplumber.open(str(path)) as pdf:
#                 # Try extracting as a layout first; if empty, use raw text
#                 text = "\n".join([p.extract_text(layout=True) or p.extract_text() or "" for p in pdf.pages])
#                 # If still empty, the file might be complex; try to get raw chars
#                 if not text.strip():
#                     text = "\n".join([p.extract_text(x_tolerance=2) for p in pdf.pages])
                    
#         elif path.suffix.lower() in [".docx", ".doc"]:
#             with open(str(path), "rb") as f:
#                 text = mammoth.extract_raw_text(f).value
#     except Exception as e:
#         return {"extracted_data": {"error": f"File read error: {str(e)}"}}

#     # The rest of your logic (Prompt, Groq call, JSON repair) stays exactly the same
    
# builder = StateGraph(ResumePathState)
# builder.add_node("extract", load_and_extract)
# builder.set_entry_point("extract")
# builder.add_edge("extract", END)
# pipeline = builder.compile()

# Async code
import os, json, re, mammoth, pdfplumber, time
from pathlib import Path
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from typing import TypedDict

# Initialize Groq
llm = ChatGroq(model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))

class ResumePathState(TypedDict):
    file_path: str
    extracted_data: dict

async def invoke_with_retry_async(prompt, retries=5):
    """Exponential backoff to handle Rate Limits (429)."""
    for i in range(retries):
        try:
            return await llm.ainvoke(prompt)
        except Exception as e:
            if "429" in str(e):
                sleep_time = 10 * (2 ** i)
                time.sleep(sleep_time)
            else:
                raise e
    return await llm.ainvoke(prompt)

async def load_and_extract(state: ResumePathState) -> dict:
    # ... (Keep your existing PDF/Word extraction logic) ...

    prompt = f"""
    CRITICAL: Extract data from the resume below.
    Return ONLY a raw JSON string. DO NOT include any text before or after the JSON. 
    DO NOT use markdown formatting.
    
    Fields: "name", "email", "location", "total_exp", "recent_company", "recent_designation", "prev_company", "prev_designation".
    If data is missing, return "".
    
    Resume Text:
    {text[:8000]}
    """
    
    # Use our existing async invoke
    response = await invoke_with_retry_async(prompt)
    content = response.content
    
    # NEW: Aggressive Sanitization
    # Strip everything up to the first '{' and after the last '}'
    start_index = content.find('{')
    end_index = content.rfind('}') + 1
    
    if start_index != -1 and end_index != -1:
        clean_json = content[start_index:end_index]
        try:
            return {"extracted_data": json.loads(clean_json)}
        except:
            return {"extracted_data": {"error": "JSON Parse Error: Malformed JSON"}}
    else:
        return {"extracted_data": {"error": "JSON Parse Error: No JSON found"}}

builder = StateGraph(ResumePathState)
builder.add_node("extract", load_and_extract)
builder.set_entry_point("extract")
builder.add_edge("extract", END)
pipeline = builder.compile()