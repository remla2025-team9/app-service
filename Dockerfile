FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./

RUN pip install https://github.com/remla2025-team9/lib-version/archive/refs/tags/a1.zip
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

COPY . .

ARG APP_VERSION=NOT_SET
ENV APP_VERSION=${APP_VERSION}
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
ENV FLASK_DEBUG=0

EXPOSE 5000

CMD ["python", "src/main.py"]
