# OpenNEM Energy Market Data Access

The OpenNEM project aims to make the wealth of public National Electricity Market (NEM) data more accessible to a wider audience.

This toolkit enables downloading, mirroring and accessing energy data from various networks

Currently supports:

- Australian NEM
- West Australia Energy Market

## Install

You can install this project with python `pip`:

```sh
$ pip install opennem
```

## Usage

List the crawlers

```sh
$ opennem list
```

Crawl

```sh
$ opennem crawl au.nem.current.dispatch_scada
```

## Development

Code:

```sh
$ poetry install
$ source .venv/bin/activate
```

There is a `docker-compose` file that will bring a local database:

```sh
$ docker-compose up -d
```
