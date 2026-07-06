import streamlit as st
import os
import pandas as pd
from pathlib import Path
from io import BytesIO
import tempfile
import time

# Load API key — works locally and on Streamlit Cloud
if not os.getenv("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

from processing import pipeline

BATCH_SIZE = 25
BATCH_PAUSE = 65

st.set_page_config(page_title="Manalot AI Portal", layout="wide")
st.title("📄 Resume Extraction Portal")

uploaded_files = st.file_uploader(
    "Upload Resumes (PDF or Word) — up to 300 files",
    accept_multiple_files=True,
    type=["pdf", "docx", "doc"]
)

if uploaded_files:
    batches_needed = (len(uploaded_files) // BATCH_SIZE) + 1
    est_minutes = batches_needed * 1.5
    st.info(f"{len(uploaded_files)} file(s) uploaded — "
            f"estimated time: ~{est_minutes:.0f} minute(s).")

if st.button("🚀 Process Resumes"):
    if not uploaded_files:
        st.warning("Please upload files first.")
    else:
        results = []
        errors = []
        progress = st.progress(0)
        status = st.empty()
        batch_status = st.empty()
        total = len(uploaded_files)

        batches = [
            uploaded_files[i:i + BATCH_SIZE]
            for i in range(0, total, BATCH_SIZE)
        ]

        for batch_num, batch in enumerate(batches):

            # Pause between batches for rate limit reset
            if batch_num > 0:
                for remaining in range(BATCH_PAUSE, 0, -1):
                    batch_status.info(
                        f"Batch {batch_num}/{len(batches)} done. "
                        f"Rate limit cooldown: {remaining}s..."
                    )
                    time.sleep(1)
                batch_status.empty()

            batch_status.info(
                f"Processing batch {batch_num + 1} of {len(batches)} "
                f"({len(batch)} resumes)..."
            )

            for f in batch:
                status.text(f"Processing: {f.name}")
                suffix = Path(f.name).suffix

                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(f.getbuffer())
                    tmp_path = Path(tmp.name)

                try:
                    res = pipeline.invoke({"file_path": str(tmp_path)})
                    results.append(res["extracted_data"])
                    st.success(f"✓ {f.name}")

                except Exception as e:
                    errors.append(f.name)
                    st.error(f"✗ {f.name}: {str(e)}")

                finally:
                    if tmp_path.exists():
                        tmp_path.unlink()

                progress.progress((len(results) + len(errors)) / total)

        status.text("All done!")
        batch_status.empty()

        if errors:
            st.warning(f"{len(errors)} file(s) failed: {', '.join(errors)}")

        if results:
            rows = []