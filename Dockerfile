FROM ghcr.io/civicactions/pyction:latest

COPY pyproject.toml uv.lock ./
ENV UV_PROJECT_ENVIRONMENT=/tmp/venv
RUN uv sync --no-dev

WORKDIR /app
COPY . .

EXPOSE 5000

ENV FLASK_APP=app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# nosemgrep: dockerfile.security.missing-user.missing-user
ENTRYPOINT ["./entrypoint.sh"]
