FROM python:3.11-slim

WORKDIR /app

RUN apt update && apt install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt setup.py ./
COPY src/ src/

RUN pip install --upgrade pip \
 && pip install "lib_version @ git+https://github.com/remla2025-team9/lib-version.git@a1#egg=lib_version" \
 && pip install --no-cache-dir -r requirements.txt \
 && pip install .

COPY . .

ARG APP_VERSION=NOT_SET
ENV APP_VERSION=${APP_VERSION} \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=5000 \
    FLASK_DEBUG=0

EXPOSE 5000
CMD ["python", "-m", "src.main"]
