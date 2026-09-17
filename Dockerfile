FROM python:3.11-slim

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

# Run as non-root — small but real security practice worth calling out in your README
RUN useradd -m appuser
USER appuser

EXPOSE 5000

CMD ["python", "app.py"]