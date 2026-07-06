import streamlit as st
import pandas as pd
from pathlib import Path
import os
import shutil
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
            
            try:
                # Run Pipeline
                res = pipeline.invoke({"file_path": str(temp_path)})
                st.session_state.results.append(res["extracted_data"])
            except Exception as e:
                st.error(f"Failed to process {file.name}: {e}")
            finally:
                # Cleanup temp file
                if temp_path.exists():
                    os.remove(temp_path)
            
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        status_text.text("Extraction Complete!")

# Display Results
if st.session_state.results:
    df = pd.DataFrame(st.session_state.results)
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download CSV", csv, "results.csv", "text/csv")