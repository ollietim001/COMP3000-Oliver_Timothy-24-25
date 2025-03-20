FROM python:3.10-slim
WORKDIR /app
COPY src/ /app
COPY requirements.txt /app
RUN pip install -r requirements.txt
EXPOSE 5001
CMD ["sh", "-c", "gunicorn -w $((2 * $(nproc) + 1)) --worker-class gevent --timeout 120 --preload -b 0.0.0.0:5001 app:app"]
ENV PYTHONUNBUFFERED=1
