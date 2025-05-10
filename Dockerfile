FROM python:3.11-slim

WORKDIR /app

RUN apt update && apt install -y git && rm -rf /var/lib/apt/lists/*

COPY setup.py .
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install . \
    && pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

COPY . .

ARG APP_VERSION=NOT_SET
ENV APP_VERSION=${APP_VERSION}
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
ENV FLASK_DEBUG=0
ENV PYTHONPATH=/app/lib-version

EXPOSE 5000

CMD ["python", "src/main.py"]
