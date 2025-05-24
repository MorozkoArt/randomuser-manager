FROM ubuntu:22.04

WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3.11 /usr/bin/python

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY main.py .
COPY ./app /app/app

ENV PYTHONPATH=/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]