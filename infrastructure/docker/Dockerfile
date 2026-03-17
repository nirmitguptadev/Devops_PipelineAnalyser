FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Copy configuration files (the * ignores if they are missing locally)
COPY settings.json* .

EXPOSE 5000

ENV FLASK_APP=src/main/app.py
ENV PYTHONUNBUFFERED=1

CMD ["python", "src/main/app.py"]
