FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app

ENV PYTHONPATH=/app
ENV PORT=8002
EXPOSE 8002

USER appuser

CMD ["sh", "scripts/start.sh"]
