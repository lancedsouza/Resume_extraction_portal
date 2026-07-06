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

def load_and_extract(state: ResumePathState) -> dict:
    path = Path(state["file_path"])
    text = ""
    
    # PDF Extraction
    if path.suffix.lower() == ".pdf":
        with pdfplumber.open(str(path)) as pdf:
            # Using list comprehension to safely extract text
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])
            
    # DOCX/DOC Extraction
    elif path.suffix.lower() in [".docx", ".doc"]:
        with open(str(path), "rb") as f:
            # Mammoth.extract_raw_text returns an object with a .value attribute
            result = mammoth.extract_raw_text(f)
            text = result.value
            
    # AI Extraction
    MAX_CHARS = 15000 
    truncated_text = text[:MAX_CHARS]
    
    prompt = f"Extract resume info to JSON: {truncated_text}"
    response = llm.invoke(prompt).content
    match = re.search(r'\{.*\}', response, re.DOTALL)
    data = json.loads(match.group()) if match else {}
    
    return {"extracted_data": data}

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