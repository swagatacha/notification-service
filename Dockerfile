FROM python:3.9-slim-buster

COPY . /appdata
WORKDIR /appdata
RUN apt update && apt install -y curl
RUN pip3 install -r requirements.txt

ENV HOST=${HOST:-0.0.0.0}
ENV PORT=${PORT:-8000}

CMD ["bash", "-c", "python3 rabbitmq_queue_setup.py && uvicorn main:app --host ${HOST} --port ${PORT}"]

