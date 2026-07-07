# import streamlit as st
# import pandas as pd
# from pathlib import Path
# import os
# import shutil
# from processing import pipeline

# # Configure Page
# st.set_page_config(page_title="Manalot | AI Resume Scout", layout="wide")
# st.title("📄 Manalot AI Resume Scout")

# # 1. FIX: Use a local folder instead of /app/data
# # Use a relative path! This creates a folder inside your app's directory.
# DATA_DIR = Path("data") 
# DATA_DIR.mkdir(exist_ok=True)

# # Initialize Session State
# if 'results' not in st.session_state:
#     st.session_state.results = []

# uploaded_files = st.file_uploader("Upload Resumes", accept_multiple_files=True, type=['pdf', 'docx', 'doc'])

# if st.button("🚀 Start Extraction"):
#     if not uploaded_files:
#         st.warning("Please upload files first.")
#     else:
#         progress_bar = st.progress(0)
#         status_text = st.empty()
        
#         for i, file in enumerate(uploaded_files):
#             status_text.text(f"Analyzing {file.name}...")
            
#             # Save file to local 'data/' folder
#             temp_path = DATA_DIR / file.name
#             with open(temp_path, "wb") as f:
#                 f.write(file.getbuffer())
            
#             try:
#                 # Run Pipeline
#                 res = pipeline.invoke({"file_path": str(temp_path)})
#                 st.session_state.results.append(res["extracted_data"])
#             except Exception as e:
#                 st.error(f"Failed to process {file.name}: {e}")
#             finally:
#                 # Cleanup temp file
#                 if temp_path.exists():
#                     os.remove(temp_path)
            
#             progress_bar.progress((i + 1) / len(uploaded_files))
        
#         status_text.text("Extraction Complete!")

# # Display Results
# if st.session_state.results:
#     df = pd.DataFrame(st.session_state.results)
#     st.dataframe(df, use_container_width=True)
#     csv = df.to_csv(index=False).encode('utf-8')
#     st.download_button("⬇️ Download CSV", csv, "results.csv", "text/csv")
# Code from Claud

# import streamlit as st
# import os
# import pandas as pd
# from pathlib import Path
# from io import BytesIO
# import tempfile
# import time

# if not os.getenv("GEMINI_API_KEY"):
#     os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

# from processing import pipeline

# BATCH_SIZE = 25
# BATCH_PAUSE = 65

# st.set_page_config(page_title="Manalot AI Portal", layout="wide")
# st.title("📄 Resume Extraction Portal")

# uploaded_files = st.file_uploader(
#     "Upload Resumes (PDF or Word)",
#     accept_multiple_files=True,
#     type=["pdf", "docx", "doc"]
# )

# if uploaded_files:
#     batches_needed = (len(uploaded_files) // BATCH_SIZE) + 1
#     st.info(f"{len(uploaded_files)} file(s) uploaded — "
#             f"estimated time: ~{batches_needed * 2} minute(s).")

# if st.button("🚀 Process Resumes"):
#     if not uploaded_files:
#         st.warning("Please upload files first.")
#     else:
#         results = []
#         errors = []
#         progress = st.progress(0)
#         status = st.empty()
#         batch_status = st.empty()
#         total = len(uploaded_files)
#         batches = [uploaded_files[i:i+BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]

#         for batch_num, batch in enumerate(batches):
#             if batch_num > 0:
#                 for remaining in range(BATCH_PAUSE, 0, -1):
#                     batch_status.info(f"Cooldown: {remaining}s before next batch...")
#                     time.sleep(1)
#                 batch_status.empty()

#             batch_status.info(f"Batch {batch_num+1}/{len(batches)} — {len(batch)} resumes...")

#             for f in batch:
#                 status.text(f"Processing: {f.name}")
#                 suffix = Path(f.name).suffix

#                 with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
#                     tmp.write(f.getbuffer())
#                     tmp_path = Path(tmp.name)

#                 try:
#                     res = pipeline.invoke({"file_path": str(tmp_path)})
#                     results.append(res["extracted_data"])
#                     st.success(f"✓ {f.name}")

#                 except Exception as e:
#                     errors.append(f.name)
#                     st.error(f"✗ {f.name}: {str(e)}")

#                 finally:
#                     if tmp_path.exists():
#                         tmp_path.unlink()

#                 progress.progress((len(results) + len(errors)) / total)

#         status.text("All done!")
#         batch_status.empty()

#         if errors:
#             st.warning(f"{len(errors)} failed: {', '.join(errors)}")

#         if results:
#             rows = []
#             for i, data in enumerate(results, start=1):
#                 rows.append({
#                     "Sr No": i,
#                     "Name": data.get("name", ""),
#                     "Company": data.get("Company_1", ""),
#                     "Designation": data.get("Designation_1", ""),
#                     "Work Experience": data.get("Work_experience", ""),
#                     "Location": data.get("Location", ""),
#                     "Contact": data.get("Contact_no", ""),
#                     "Email": data.get("email", "")
#                 })
#                 rows.append({
#                     "Sr No": None, "Name": None,
#                     "Company": data.get("Company_2", ""),
#                     "Designation": data.get("Designation_2", ""),
#                     "Work Experience": None,
#                     "Location": None, "Contact": None, "Email": None
#                 })

#             df = pd.DataFrame(rows)

#             # Convert all columns to string to avoid pyarrow type errors
#             df = df.astype(object)

#             st.dataframe(df)

#             buffer = BytesIO()
#             df.to_excel(buffer, index=False)
#             buffer.seek(0)

#             st.download_button(
#                 "⬇️ Download Master Excel",
#                 buffer,
#                 "extracted_resumes.xlsx",
#                 "application/vnd.ms-excel"
#             )
# # Code from qwen
# import streamlit as st
# import pandas as pd
# from pathlib import Path
# import os
# import shutil
# import time 
# from processing import pipeline

# # Configure Page
# st.set_page_config(page_title="Manalot | AI Resume Scout", layout="wide")
# st.title("📄 Manalot AI Resume Scout")

# # 1. FIX: Use a local folder instead of /app/data
# # Use a relative path! This creates a folder inside your app's directory.
# DATA_DIR = Path("data") 
# DATA_DIR.mkdir(exist_ok=True)

# # Initialize Session State
# if 'results' not in st.session_state:
#     st.session_state.results = []

# uploaded_files = st.file_uploader("Upload Resumes", accept_multiple_files=True, type=['pdf', 'docx', 'doc'])

# if st.button("🚀 Start Extraction"):
#     if not uploaded_files:
#         st.warning("Please upload files first.")
#     else:
#         progress_bar = st.progress(0)
#         status_text = st.empty()
        
#         for i, file in enumerate(uploaded_files):
#             status_text.text(f"Analyzing {file.name}...")
            
#             # Save file to local 'data/' folder
#             temp_path = DATA_DIR / file.name
#             with open(temp_path, "wb") as f:
#                 f.write(file.getbuffer())
            
#             # --- RETRY LOGIC WITH EXPONENTIAL BACKOFF ---
#             max_retries = 4
#             processed = False
            
#             for attempt in range(max_retries):
#                 try:
#                     # Run Pipeline
#                     res = pipeline.invoke({"file_path": str(temp_path)})
#                     st.session_state.results.append(res["extracted_data"])
#                     processed = True
#                     break # Success, exit the retry loop
#                 except Exception as e:
#                     error_msg = str(e)
#                     # Check if the error is specifically a rate limit (429)
#                     if "rate_limit_exceeded" in error_msg or "429" in error_msg:
#                         # Wait 5s, then 10s, then 20s, then 40s
#                         wait_time = 5 * (2 ** attempt) 
#                         st.warning(f"⏳ Rate limit hit for {file.name}. Waiting {wait_time}s and retrying ({attempt+1}/{max_retries})...")
#                         time.sleep(wait_time)
#                     else:
#                         st.error(f"Failed to process {file.name}: {e}")
#                         break # If it's a different error, stop retrying
            
#             if not processed:
#                 st.error(f"Skipped {file.name} after {max_retries} retries.")
#             # ------------------------------------------
            
#             # Cleanup temp file
#             if temp_path.exists():
#                 os.remove(temp_path)
            
#             # ADD A SMALL DELAY BETWEEN FILES
#             # This spaces out your requests so you don't hit the 6000 TPM limit as quickly
#             time.sleep(1.5) 
            
#             progress_bar.progress((i + 1) / len(uploaded_files))
        
#         status_text.text("Extraction Complete!")

# # --- DISPLAY RESULTS (FIXED FOR PYARROW CRASH) ---
# if st.session_state.results:
#     df = pd.DataFrame(st.session_state.results)
    
#     # FIX: Convert all columns to strings to prevent PyArrow crashes 
#     # when the LLM returns nested JSON (lists/dicts) in the dataframe
#     df_display = df.astype(str)
    
#     st.dataframe(df_display, use_container_width=True)
    
#     # For the CSV download, we use the original df so Excel/CSV parsers 
#     # can still attempt to read the raw data if needed
#     csv = df.to_csv(index=False).encode('utf-8')
#     st.download_button("⬇️ Download CSV", csv, "results.csv", "text/csv")

# Code from Gemini
import streamlit as st
import os, time, tempfile
import pandas as pd
from pathlib import Path
from io import BytesIO
from processing import pipeline

st.set_page_config(page_title="Resume Portal", layout="wide")
st.title("📄 Resume Extraction Portal")

uploaded_files = st.file_uploader("Upload Resumes", accept_multiple_files=True, type=["pdf", "docx", "doc"])

if st.button("🚀 Process Resumes"):
    results = []
    for f in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(f.name).suffix) as tmp:
            tmp.write(f.getbuffer())
            tmp_path = tmp.name
        
        try:
            res = pipeline.invoke({"file_path": tmp_path})
            results.append(res["extracted_data"])
            st.success(f"✓ {f.name}")
            time.sleep(1)
        except Exception as e:
            st.error(f"✗ {f.name}: {e}")
        finally:
            if os.path.exists(tmp_path): os.remove(tmp_path)

    if results:
        # Map to your required format
        df = pd.DataFrame([{
            "Name": r.get("name"),
            "Email": r.get("email"),
            "Contact": r.get("contact"),
            "Location": r.get("location"),
            "Total Exp (Years)": r.get("total_experience_years"),
            "Most Recent Company": r.get("company_1"),
            "Most Recent Designation": r.get("designation_1"),
            "Previous Company": r.get("company_2"),
            "Previous Designation": r.get("designation_2")
        } for r in results])
        
        st.dataframe(df, use_container_width=True)
        
        buffer = BytesIO()
        df.to_excel(buffer, index=False)
        st.download_button("⬇️ Download Excel", buffer.getvalue(), "resumes.xlsx")