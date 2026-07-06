import streamlit as st
import os
import pandas as pd
from pathlib import Path
from io import BytesIO
import tempfile
import time
import traceback


if not os.getenv("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

from processing import pipeline

st.set_page_config(page_title="Manalot AI Portal", layout="wide")
st.title("📄 Resume Extraction Portal")

uploaded_files = st.file_uploader(
    "Upload Resumes (PDF or Word)",
    accept_multiple_files=True,
    type=["pdf", "docx", "doc"]
)

if st.button("🚀 Process Resumes"):
    if not uploaded_files:
        st.warning("Please upload files first.")
    else:
        results = []
        errors = []
        progress = st.progress(0)
        status = st.empty()

        for i, f in enumerate(uploaded_files):
            status.text(f"Processing {f.name}...")
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
                st.code(traceback.format_exc())  # ← shows full traceback in the UIThat way you don't need to dig through logs — the full error prints right on screen when a file fails.
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()

            progress.progress((i + 1) / len(uploaded_files))
            time.sleep(1)

        status.text("Done!")

        if errors:
            st.warning(f"{len(errors)} file(s) failed.")

        if results:
            rows = []
            for i, data in enumerate(results, start=1):
                rows.append({
                    "Sr No": i,
                    "Name": data["name"],
                    "Company": data["Company_1"],
                    "Designation": data["Designation_1"],
                    "Work Experience": data["Work_experience"],
                    "Location": data["Location"],
                    "Contact": data["Contact_no"],
                    "Email": data["email"]
                })
                rows.append({
                    "Sr No": None, "Name": None,
                    "Company": data["Company_2"],
                    "Designation": data["Designation_2"],
                    "Work Experience": None, "Location": None,
                    "Contact": None, "Email": None
                })

            df = pd.DataFrame(rows)
            st.dataframe(df, width='stretch')
            buffer = BytesIO()
            df.to_excel(buffer, index=False)
            buffer.seek(0)

            st.download_button(
                "⬇️ Download Master Excel",
                buffer,
                "extracted_resumes.xlsx",
                "application/vnd.ms-excel"
            )