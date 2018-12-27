FROM python:3.6-alpine as base

FROM base as builder

RUN mkdir /src
WORKDIR /src

RUN apk --update add build-base

COPY requirements.txt /src/requirements.txt

RUN pip install --install-option="--prefix=/install" -r requirements.txt

FROM base

COPY --from=builder /install /usr/local

COPY . /code
WORKDIR /code

ENTRYPOINT [ "python3", "/code/app.py" ]
