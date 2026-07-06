import streamlit as st
import pandas as pd
from redis import Redis
from rq import Queue
from pathlib import Path
import os

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
redis_conn = Redis(host=REDIS_HOST, port=6379)
q = Queue("resume_tasks", connection=redis_conn)

DATA_DIR = Path("/app/data")
EXCEL_PATH = DATA_DIR / "master_resume_data.xlsx"
DATA_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Manalot AI Portal", layout="wide")
st.title("📄 Resume Extraction Portal")

tab1, tab2 = st.tabs(["📤 Upload & Queue", "📊 View Master Database"])

with tab1:
    st.subheader("Submit Resumes for Processing")
    uploaded_files = st.file_uploader(
        "Upload Resumes (PDF/Word)",
        accept_multiple_files=True,
        type=["pdf", "docx", "doc"]
    )

    if st.button("🚀 Submit to Queue"):
        if not uploaded_files:
            st.warning("Please upload files first.")
        else:
            for f in uploaded_files:
                save_path = DATA_DIR / f.name
                with open(save_path, "wb") as out:
                    out.write(f.getbuffer())
                q.enqueue("worker.pipeline_wrapper", str(save_path))

            st.success(f"Queued {len(uploaded_files)} file(s). Check the database tab once done.")

with tab2:
    st.subheader("Master Resume Database")
    if st.button("🔄 Refresh"):
        if EXCEL_PATH.exists():
            df = pd.read_excel(EXCEL_PATH)
            st.dataframe(df, use_container_width=True)
            with open(EXCEL_PATH, "rb") as f:
                st.download_button(
                    "⬇️ Download Master Excel",
                    f,
                    "master_extracted_data.xlsx"
                )
        else:
            st.info("No data yet — wait for workers to finish.")

st.sidebar.title("System Status")
st.sidebar.metric("Tasks in Queue", len(q))