ARG PYTHON_VERSION=3.13-alpine

# Builder
FROM python:${PYTHON_VERSION} AS builder

RUN pip install --upgrade pip

WORKDIR /app

COPY requirements.txt ./
RUN python -m venv .env
ENV PATH="/app/.env/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py ./

# Production
FROM python:${PYTHON_VERSION}

RUN apk update && \
    apk add --no-cache gnupg && \
    rm -rf /var/cache/apk/*

RUN adduser -D signer

RUN mkdir -p /sigs && chown signer:signer /sigs
VOLUME ["/repo", "/sigs"]

WORKDIR /app
COPY --from=builder --chown=signer:signer /app .

USER signer
EXPOSE 5000

ENV PATH="/app/.env/bin:$PATH"
CMD ["gunicorn", "-w 3", "-t 60", "-b 0.0.0.0:5000", "app:app"]