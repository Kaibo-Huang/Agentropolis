FROM astral/uv:python3.12-bookworm-slim

WORKDIR /app

COPY . .

RUN uv sync --no-dev

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
