FROM python:3.8.0-alpine3.10

WORKDIR /app

COPY requirements.txt /app
COPY main.py /app

RUN python3 -m pip install -r requirements.txt

CMD ["python3", "main.py"]
