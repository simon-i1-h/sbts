FROM python:3 AS base

ENV LANG=C.UTF-8
RUN useradd -m app
RUN apt-get update && apt-get -y install gosu postgresql-client awscli
RUN pip install pipenv

USER app
WORKDIR /home/app

RUN echo >> /home/app/.profile \
	&& echo 'export LANG=C.UTF-8' >> /home/app/.profile

COPY Pipfile /home/app/Pipfile
COPY Pipfile.lock /home/app/Pipfile.lock
RUN pipenv install --system

USER root

# graceful shutdown
# https://stackoverflow.com/a/52046161
STOPSIGNAL SIGINT

CMD ["/home/app/opt/sbts/envw", "/home/app/opt/sbts/entrypoint.sh"]

# ----------------------------------------
FROM base AS dev
