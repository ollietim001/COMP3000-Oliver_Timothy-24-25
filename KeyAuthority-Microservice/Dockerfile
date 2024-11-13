FROM python:3.10-slim
WORKDIR /app
COPY src/ /app
COPY requirements.txt /app
RUN pip install -r requirements.txt
EXPOSE 5002
CMD ["python", "app.py"]
ENV PYTHONUNBUFFERED=1
