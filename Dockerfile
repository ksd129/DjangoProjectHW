FROM python:3.12

ENV PYTHONUNBUFFERED=1

ARG WORKDIR=/wd
ARG USER=user

WORKDIR ${WORKDIR}

RUN useradd --system ${USER} && \
    chown --recursive ${USER} ${WORKDIR}

RUN apt update && apt upgrade --yes

COPY --chown=${USER} requirements.txt requirements.txt

RUN pip install --upgrade pip && \
    pip install --requirement requirements.txt

COPY --chown=${USER} --chmod=555 docker/app/entrypoint.sh /entrypoint.sh
COPY --chown=${USER} --chmod=555 docker/app/start.sh /start.sh
COPY --chown=${USER} --chmod=555 docker/app/init.sh /init.sh
COPY --chown=${USER} --chmod=555 docker/app/celery_worker_start.sh /celery_worker_start.sh
COPY --chown=${USER} --chmod=555 docker/app/celery_beat_start.sh /celery_beat_start.sh


COPY --chown=${USER} Makefile Makefile
COPY --chown=${USER} manage.py manage.py
COPY --chown=${USER} core core
COPY --chown=${USER} apps/cryptocurrency_wi cryptocurrency_wi
