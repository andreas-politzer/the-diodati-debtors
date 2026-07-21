# Official Reflex single-container deployment pattern, for platforms
# like Railway/Render/Heroku: Caddy reverse-proxies backend routes,
# serves the static frontend directly, TLS handled by the platform.
FROM python:3.11-slim-bookworm

ARG PORT=8080
ARG API_URL
ENV PORT=$PORT API_URL=${API_URL:-http://localhost:$PORT}

RUN apt-get update -y && apt-get install -y caddy unzip curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN cat > Caddyfile <<EOF
:{\$PORT}

encode gzip

@backend_routes path /_event/* /ping /_upload /_upload/*
handle @backend_routes {
	reverse_proxy localhost:8000
}

root * /srv
route {
	try_files {path} {path}/ /404.html
	file_server
}
EOF

COPY . .

RUN pip install -r requirements.txt --break-system-packages

RUN reflex init

RUN reflex export --frontend-only --no-zip && mv .web/_static/* /srv/ && rm -rf .web

STOPSIGNAL SIGKILL

EXPOSE $PORT

CMD [ -d alembic ] && reflex db migrate; \
    caddy start && reflex run --env prod --backend-only --loglevel debug