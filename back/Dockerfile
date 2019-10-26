FROM python:3.6-alpine as base

FROM base as builder

RUN mkdir /src
WORKDIR /src

RUN apk --update add build-base postgresql-client postgresql-dev bash libxml2 libxml2-dev libxslt-dev

COPY requirements.txt /src/requirements.txt

RUN pip install -r requirements.txt

FROM base

RUN apk --update add postgresql-client libxml2 libxslt redis

COPY --from=builder /usr/local /usr/local

COPY . /code
WORKDIR /code

COPY wait-for-it.sh /
COPY entrypoint.sh /
# ENV FLASK_APP=app.py
# CMD flask run

