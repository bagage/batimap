FROM python:3.6-alpine
RUN apk --update add build-base postgresql-client postgresql-dev bash libxml2 libxml2-dev libxslt-dev

ADD . /code
WORKDIR /code

RUN pip install -r requirements.txt

COPY wait-for-it.sh /
# ENV FLASK_APP=app.py
# CMD flask run

