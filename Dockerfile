FROM python:3.11-slim

# Install system dependencies (LibreOffice for Word-to-PDF)
RUN apt-get update && apt-get install -y libreoffice && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .

# Install dependencies globally
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501"]