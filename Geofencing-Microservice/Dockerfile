FROM python:3.10-slim
WORKDIR /app
COPY src/ /app
COPY requirements.txt /app
RUN pip install -r requirements.txt
EXPOSE 5001
CMD ["python", "app.py"]
ENV PYTHONUNBUFFERED=1
