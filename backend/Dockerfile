FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app

ENV PYTHONPATH=/app
ENV PORT=8001

EXPOSE 8001

USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
