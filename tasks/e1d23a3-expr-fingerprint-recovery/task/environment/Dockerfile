# Single container image — agent run + verifier (canonical TB2)
FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

# Verifier deps (pinned, baked at build time)
RUN pip install --no-cache-dir --break-system-packages pytest==8.4.1 pytest-json-ctrf==0.3.5

# Seed data — the 20 archived expression-signature pairs
COPY data /app/data

RUN mkdir -p /app
WORKDIR /app
