FROM node:alpine

RUN apk --update add git yarn

ADD . /usr/src/app

RUN chown -R node:node /usr/src/app

WORKDIR /usr/src/app
CMD yarn && yarn start --host 0.0.0.0

