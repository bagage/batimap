FROM node:16-alpine

RUN apk --update add git yarn

ADD . /usr/src/app

RUN mkdir /usr/src/app/node_modules

RUN chown -R node:node /usr/src/app

VOLUME /usr/src/app/node_modules

WORKDIR /usr/src/app

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
CMD yarn && yarn start --host 0.0.0.0

