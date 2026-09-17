FROM python:3.11-slim

# Patch OS-level packages (perl, sqlite, pcre2, gzip, etc. from the base image)
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY app/requirements.txt .
# Upgrade pip/setuptools/wheel themselves before installing anything else
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

RUN useradd -m appuser
USER appuser

EXPOSE 5000

CMD ["python", "app.py"]