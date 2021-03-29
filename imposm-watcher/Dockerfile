FROM python:3.9-alpine as base

FROM base as builder

RUN mkdir /src
WORKDIR /src

RUN apk --update add build-base

COPY Pipfile* /src/

RUN pip install pipenv && pipenv lock -r > requirements.txt && pip install -r requirements.txt

FROM base

COPY --from=builder /usr/local /usr/local

COPY . /code
WORKDIR /code

ENTRYPOINT [ "python3", "/code/app.py" ]
