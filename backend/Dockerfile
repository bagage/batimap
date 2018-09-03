FROM python:3.6-alpine
RUN apk --update add build-base postgresql-dev bash libxml2 libxml2-dev libxslt-dev
ADD . /code
WORKDIR /code

COPY wait-for-it.sh /

RUN pip install -r requirements.txt
# ENV FLASK_APP=app.py
# CMD flask run

