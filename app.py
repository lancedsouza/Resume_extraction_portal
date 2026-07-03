# import streamlit as st
# import subprocess
# import os
# import pandas as pd
# from pathlib import Path
# from io import BytesIO
# from processing import pipeline  # import your compiled graph from data.py

# st.set_page_config(page_title="Manalot Resume Processor", layout="wide")
# st.title("📄 Resume Extraction Portal")

# uploaded_files = st.file_uploader(
#     "Upload Resumes (PDF/Word)",
#     accept_multiple_files=True,
#     type=['pdf', 'docx', 'doc']
# )

# if st.button("Process Resumes"):
#     if not uploaded_files:
#         st.warning("Please upload files first.")
#     else:
#         results = []
#         errors = []

#         with st.spinner("Processing..."):
#             for uploaded_file in uploaded_files:
#                 try:
#                     # 1. Save to temp file
#                     temp_path = Path(f"temp_{uploaded_file.name}")
#                     with open(temp_path, "wb") as f:
#                         f.write(uploaded_file.getbuffer())

#                     # 2. Convert Word to PDF if needed
#                     final_path = temp_path
#                     if temp_path.suffix in [".docx", ".doc"]:
#                         subprocess.run(
#                             ['soffice', '--headless', '--convert-to', 'pdf', str(temp_path)],
#                             check=True
#                         )
#                         final_path = Path(str(temp_path).rsplit('.', 1)[0] + ".pdf")

#                     # 3. Run pipeline
#                     res = pipeline.invoke({"file_path": str(final_path)})
#                     results.append(res["extracted_data"])
#                     st.success(f"✓ {uploaded_file.name}")

#                 except Exception as e:
#                     errors.append(f"✗ {uploaded_file.name}: {str(e)}")
#                     st.error(f"Failed: {uploaded_file.name}")

#                 finally:
#                     # 4. Cleanup temp files always
#                     if temp_path.exists():
#                         os.remove(temp_path)
#                     if final_path != temp_path and final_path.exists():
#                         os.remove(final_path)

#         if errors:
#             st.warning(f"{len(errors)} file(s) failed. Check errors above.")

#         if results:
#             # 5. Build Excel and offer download
#             df = pd.DataFrame(results)
#             st.dataframe(df)   # preview in UI

#             buffer = BytesIO()
#             df.to_excel(buffer, index=False)
#             buffer.seek(0)     # ← critical

#             st.download_button(
#                 label="⬇️ Download Master Excel",
#                 data=buffer,
#                 file_name="extracted_resumes.xlsx",
#                 mime="application/vnd.ms-excel"
#             )

import streamlit as st
import subprocess
import os
import pandas as pd
from pathlib import Path
from io import BytesIO
from processing import pipeline
import time

# API key check for Streamlit Cloud
if not os.getenv("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

st.set_page_config(page_title="Manalot Resume Processor", layout="wide")
st.title("📄 Resume Extraction Portal")

uploaded_files = st.file_uploader(
    "Upload Resumes (PDF/Word)",
    accept_multiple_files=True,
    type=['pdf', 'docx', 'doc']
)

if st.button("Process Resumes"):
    if not uploaded_files:
        st.warning("Please upload files first.")
    else:
        results = []
        errors = []

        with st.spinner("Processing..."):
            for uploaded_file in uploaded_files:
                time.sleep(1.0)  # slight delay to avoid overwhelming the system
                temp_path = Path(f"temp_{uploaded_file.name}")
                final_path = temp_path
                try:
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    if temp_path.suffix in [".docx", ".doc"]:
                        subprocess.run(
                            ['soffice', '--headless', '--convert-to', 'pdf', str(temp_path)],
                            check=True
                        )
                        final_path = Path(str(temp_path).rsplit('.', 1)[0] + ".pdf")

                    res = pipeline.invoke({"file_path": str(final_path)})
                    results.append(res["extracted_data"])
                    st.success(f"✓ {uploaded_file.name}")

                except Exception as e:
                    errors.append(str(e))
                    st.error(f"✗ {uploaded_file.name}: {str(e)}")

                finally:
                    if temp_path.exists(): os.remove(temp_path)
                    if final_path != temp_path and final_path.exists(): os.remove(final_path)

        if errors:
            st.warning(f"{len(errors)} file(s) failed.")

        if results:
            # Build two rows per candidate
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
                    "Sr No": None,
                    "Name": None,
                    "Company": data["Company_2"],
                    "Designation": data["Designation_2"],
                    "Work Experience": None,
                    "Location": None,
                    "Contact": None,
                    "Email": None
                })

            df = pd.DataFrame(rows)
            st.dataframe(df)

            buffer = BytesIO()
            df.to_excel(buffer, index=False)
            buffer.seek(0)

            st.download_button(
                label="⬇️ Download Master Excel",
                data=buffer,
                file_name="extracted_resumes.xlsx",
                mime="application/vnd.ms-excel"
            )