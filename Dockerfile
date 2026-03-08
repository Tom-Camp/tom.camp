FROM node:slim AS css-builder

WORKDIR /build
COPY package.json ./
RUN npm install
COPY tailwind.config.js .
COPY app/static/css/tailwind.input.css ./app/static/css/
COPY app/templates ./app/templates/
RUN npx tailwindcss -i app/static/css/tailwind.input.css -o app/static/css/tailwind.css --minify


FROM ghcr.io/civicactions/pyction:latest

COPY pyproject.toml uv.lock ./
ENV UV_PROJECT_ENVIRONMENT=/tmp/venv
RUN uv sync --no-dev

WORKDIR /app
COPY . .
COPY --from=css-builder /build/app/static/css/tailwind.css ./app/static/css/tailwind.css

EXPOSE 5000

ENV FLASK_APP=app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# nosemgrep: dockerfile.security.missing-user.missing-user
RUN chmod +x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
