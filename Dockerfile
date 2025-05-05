FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

COPY . .

ARG APP_VERSION=unknown
ENV APP_VERSION=${APP_VERSION}

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
ENV FLASK_DEBUG=0

EXPOSE 5000

CMD ["flask", "run"]