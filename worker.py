import os
import subprocess
import pandas as pd
from pathlib import Path
from redis import Redis
from rq import Worker, Queue
from dotenv import load_dotenv
from filelock import FileLock

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
EXCEL_PATH = Path("/app/data/master_resume_data.xlsx")
LOCK_PATH = Path("/app/data/master_resume_data.lock")

def pipeline_wrapper(file_path: str):
    """Called by RQ worker for each queued file."""
    from processing import pipeline

    path = Path(file_path)
    pdf_path = path

    # Convert Word to PDF if needed
    if path.suffix in [".docx", ".doc"]:
        subprocess.run(
            ['soffice', '--headless', '--convert-to', 'pdf', str(path)],
            check=True,
            cwd=str(path.parent)
        )
        pdf_path = path.with_suffix(".pdf")

    # Run LangGraph pipeline
    result = pipeline.invoke({"file_path": str(pdf_path)})
    data = result["extracted_data"]

    # Clean up converted PDF
    if pdf_path != path and pdf_path.exists():
        pdf_path.unlink()

    # Write to Excel with file lock (prevents race conditions with multiple workers)
    with FileLock(str(LOCK_PATH)):
        try:
            df = pd.read_excel(EXCEL_PATH)
            current_sr_no = int(df["Sr No"].dropna().max()) + 1
        except FileNotFoundError:
            df = pd.DataFrame(columns=[
                "Sr No", "Name", "Company", "Designation",
                "Work Experience", "Location", "Contact", "Email"
            ])
            current_sr_no = 1

        row1 = {
            "Sr No": current_sr_no,
            "Name": data["name"],
            "Company": data["Company_1"],
            "Designation": data["Designation_1"],
            "Work Experience": data["Work_experience"],
            "Location": data["Location"],
            "Contact": data["Contact_no"],
            "Email": data["email"]
        }
        row2 = {
            "Sr No": None, "Name": None,
            "Company": data["Company_2"],
            "Designation": data["Designation_2"],
            "Work Experience": None, "Location": None,
            "Contact": None, "Email": None
        }

        df = pd.concat([df, pd.DataFrame([row1, row2])], ignore_index=True)
        df.to_excel(EXCEL_PATH, index=False)

    print(f"✓ Written: {data['name']} from {path.name}")

if __name__ == "__main__":
    redis_conn = Redis(host=REDIS_HOST, port=6379)
    q = Queue("resume_tasks", connection=redis_conn)
    w = Worker([q], connection=redis_conn)
    w.work()