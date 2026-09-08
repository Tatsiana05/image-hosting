FROM python:3.13-slim AS builder

WORKDIR /app

COPY app.py .
COPY json_tools.py .
COPY users.json .
COPY static ./static


FROM python:3.13-slim

WORKDIR /app

COPY --from=builder /app /app

CMD ["python", "app.py"]