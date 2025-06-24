FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update \
    && apt-get install -y git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

COPY . .

FROM python:3.11-slim

WORKDIR /app

ARG APP_VERSION=NOT_SET
ENV APP_VERSION=${APP_VERSION} \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=5000 \
    FLASK_DEBUG=0

COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /app/lib-version /app/lib-version
COPY --from=builder /app/src /app/src

EXPOSE 5000

CMD ["python", "src/main.py"]
