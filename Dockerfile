FROM python:3.13-slim-bookworm AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

FROM base AS builder
COPY requirements.txt /requirements.txt
RUN pip install --prefix=/install -r /requirements.txt

FROM base
RUN apt-get update \
    && apt-get install -y --no-install-recommends locales gosu procps \
    && echo 'ru_RU.UTF-8 UTF-8' > /etc/locale.gen \
    && locale-gen \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -g 800 -r unprivileged \
    && useradd -r -g 800 -u 800 -m unprivileged
ENV LANG=ru_RU.UTF-8 LC_ALL=ru_RU.UTF-8
COPY --from=builder /install /usr/local
WORKDIR /opt/app
COPY . /opt/app
RUN chmod +x entrypoint.sh wait-for-it.sh \
    && mkdir -p /opt/staticfiles /opt/media \
    && chown -R unprivileged:unprivileged /opt/app /opt/staticfiles /opt/media
EXPOSE 8000
ENTRYPOINT ["/opt/app/entrypoint.sh"]
CMD ["runserver"]
