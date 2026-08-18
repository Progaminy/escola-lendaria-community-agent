FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --no-cache-dir .

ENV PYTHONPATH=/app/src
ENV COMMUNITY_AGENT_DB=/app/data/community_agent.db

RUN mkdir -p /app/data

EXPOSE 8080

CMD ["uvicorn", "community_agent.api:app", "--host", "0.0.0.0", "--port", "8080"]
