FROM node:alpine

ARG USER_UID
ARG GROUP_UID

RUN apk --update add git yarn

ENV USER_UID ${USER_UID:-1000}
ENV GROUP_UID ${GROUP_UID:-1000}

ADD . /usr/src/app

RUN chown -R $USER_UID:$GROUP_UID /usr/src/app

USER node
WORKDIR /usr/src/app
CMD yarn && yarn start --host 0.0.0.0

