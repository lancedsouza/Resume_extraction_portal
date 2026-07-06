import streamlit as st
import pandas as pd
from pathlib import Path
import os
import time
from processing import pipeline

# Configure Page
st.set_page_config(page_title="Manalot | AI Resume Scout", layout="wide")

# Custom CSS for a professional look
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("📄 Manalot AI Resume Scout")
st.markdown("Upload your resumes, and our AI will extract the key data for your recruitment database.")

# Initialize Session State for results
if 'results' not in st.session_state:
    st.session_state.results = []

# Sidebar for controls
with st.sidebar:
    st.header("System Settings")
    st.info("Current Model: Gemini 2.0 Flash")
    if st.button("Clear History"):
        st.session_state.results = []
        st.rerun()

# Main Upload Area
uploaded_files = st.file_uploader(
    "Drag and drop resumes here", 
    accept_multiple_files=True, 
    type=['pdf', 'docx', 'doc']
)

# Processing Logic
if st.button("🚀 Start Extraction"):
    if not uploaded_files:
        st.warning("Please upload files first.")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, file in enumerate(uploaded_files):
            status_text.text(f"Analyzing {file.name} ({i+1}/{len(uploaded_files)})...")
            
            # Create temp file
            temp_path = Path(f"temp_{file.name}")
            with open(temp_path, "wb") as f:
                f.write(file.getbuffer())
            
            try:
                # Run Pipeline
                res = pipeline.invoke({"file_path": str(temp_path)})
                st.session_state.results.append(res["extracted_data"])
                st.success(f"Processed: {file.name}")
            except Exception as e:
                st.error(f"Failed to process {file.name}: {e}")
            finally:
                if temp_path.exists(): os.remove(temp_path)
                
            # Update Progress
            progress_bar.progress((i + 1) / len(uploaded_files))
            
        status_text.text("Extraction Complete!")

# Display Results Table
if st.session_state.results:
    st.subheader("Extracted Data")
    df = pd.DataFrame(st.session_state.results)
    st.dataframe(df, use_container_width=True)
    
    # Download Button
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download CSV", csv, "extracted_resumes.csv", "text/csv")