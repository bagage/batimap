FROM python:3-alpine
RUN apk --update add build-base postgresql-dev
ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt
# ENV FLASK_APP=app.py
# CMD flask run

