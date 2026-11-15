FROM python:3.12-slim
WORKDIR /app
COPY engine.py server.py ./
COPY static ./static
RUN useradd -m app && mkdir /app/data && chown app:app /app/data
USER app
ENV HOST=0.0.0.0 DB_PATH=/app/data/crisis.db
EXPOSE 8000
CMD ["python", "server.py"]
