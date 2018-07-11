FROM node:alpine
RUN apk --update add git yarn
ADD . /usr/src/app
WORKDIR /usr/src/app
RUN yarn
CMD yarn start

