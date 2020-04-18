FROM python:3.8-slim as base

FROM base as builder

RUN mkdir /src
WORKDIR /src

RUN apt update && apt install -yy --no-install-recommends gcc postgresql-client libpq-dev libxml2 libxml2-dev libxslt-dev libgeos-dev && apt clean

COPY requirements.txt /src/requirements.txt

RUN pip install -r requirements.txt

FROM base

RUN apt update && apt install -yy --no-install-recommends postgresql-client libxml2 libxslt1.1 redis && apt clean

COPY --from=builder /usr/local /usr/local

COPY . /code
WORKDIR /code

COPY wait-for-it.sh /
COPY entrypoint.sh /
