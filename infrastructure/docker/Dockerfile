FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

EXPOSE 5000

ENV FLASK_APP=src/main/app.py
ENV PYTHONUNBUFFERED=1

CMD ["python", "src/main/app.py"]
