FROM python:3.6-alpine
RUN apk --update add build-base postgresql-client postgresql-dev bash libxml2 libxml2-dev libxslt-dev

ADD requirements.txt /code/requirements.txt
WORKDIR /code

RUN pip install -r requirements.txt

ADD . /code

COPY wait-for-it.sh /
COPY entrypoint.sh /
# ENV FLASK_APP=app.py
# CMD flask run

