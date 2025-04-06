FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN mkdir /app

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt update && apt install -y netcat-openbsd
COPY requirements.txt pyproject.toml uv.lock /app/

RUN uv pip install --system -r requirements.txt


COPY entrypoint.sh /app/
COPY . /app/

EXPOSE 8000

RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]