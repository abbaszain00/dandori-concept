FROM python:3.11-slim

WORKDIR /app

COPY requirement.txt .

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["python", "app.py"]