FROM node:16-alpine
RUN apk --update add git yarn
ADD . /usr/src/app
WORKDIR /usr/src/app
RUN yarn
RUN yarn build --prod

FROM nginx:alpine
WORKDIR /usr/share/nginx/html
COPY --from=0 /usr/src/app/dist/batimap .
COPY prod/nginx.conf /etc/nginx/conf.d/default.conf
