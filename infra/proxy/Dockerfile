FROM golang:1.18-alpine

WORKDIR /app

ENV NODE_VERSION 18.3.0

RUN apk add --update nodejs npm make

ENV SLRP_VERSION 0.0.4

RUN mkdir -p /app && \
  cd /app && \
  wget -O slrp.zip "https://github.com/nfx/slrp/archive/refs/tags/v$SLRP_VERSION.zip" && \
  unzip slrp.zip && \
  cd "slrp-$SLRP_VERSION" && \
  go mod vendor && \
  npm --prefix ui install && \
  make build-ui

