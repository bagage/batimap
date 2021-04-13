FROM node:alpine

RUN apk --update add git yarn

ADD . /usr/src/app

RUN mkdir /usr/src/app/node_modules

RUN chown -R node:node /usr/src/app

VOLUME /usr/src/app/node_modules

USER node

WORKDIR /usr/src/app


CMD yarn && ng serve --host 0.0.0.0

