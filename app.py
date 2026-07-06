import streamlit as st
import uuid
from redis import Redis
from rq import Queue
from pathlib import Path

# Setup Redis connection
redis_conn = Redis(host='redis', port=6379)
q = Queue('resume_tasks', connection=redis_conn)

st.title("🚀 Manalot AI Portal (Production)")

uploaded_files = st.file_uploader("Upload Resumes", accept_multiple_files=True)

if st.button("Submit to Queue"):
    for f in uploaded_files:
        save_path = Path("/app/data") / f"{uuid.uuid4()}_{f.name}"
        with open(save_path, "wb") as out:
            out.write(f.getbuffer())
        q.enqueue('processing.pipeline_wrapper', str(save_path))
    st.success(f"Queued {len(uploaded_files)} files!")

if st.button("Refresh Data"):
    if Path("/app/data/master_resume_data.xlsx").exists():
        st.dataframe(pd.read_excel("/app/data/master_resume_data.xlsx"))