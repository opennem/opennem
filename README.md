# OpenNEM Energy Market Data Access

The OpenNEM project aims to make the wealth of public National Electricity Market (NEM) data more accessible to a wider audience.

This toolkit enables downloading, mirroring and accessing energy data from various networks

Project homepage at https://opennem.org.au

Available on Docker at https://hub.docker.com/r/opennem/opennem

Currently supports:

- Australian NEM: https://www.nemweb.com.au/
- West Australia Energy Market: http://data.wa.aemo.com.au/


## Install

You can install this project with python `pip`:

```sh
$ pip install opennem
```

Or alternatively with docker:

```
$ docker pull opennem/opennem
```

Bundled with sqlite support. Other database drivers are optional and not installed by default. Install a supported database driver:

Postgres:

```sh
$ pip install psycopg2
```

## Usage

List the crawlers

```sh
$ scrapy list
```

Crawl

```sh
$ scrapy crawl au.nem.current.dispatch_scada
```

## Development

Setting up a virtual environment and installing requiements using Poetry:

```sh
$ poetry install
$ source .venv/bin/activate
```

Settings are read from environment variables. Environment variables can be read from a `.env` file in the root of the folder. Setup the environment by copying the `.env.sample` file to `.env`. The defaults in the sample file map to the settings in `docker-compose.yml`

There is a `docker-compose` file that will bring a local database:

```sh
$ docker-compose up -d
```

Bring up the database migrations using alembic:

```sh
$ alembic upgrade head
```

Run scrapy in the root folder for options:

```sh
$ scrapy
```

The `opennem` cli interface provides other options and settings:

```sh
$ opennem -h
```

Settings for Visual Studio Code are stored in `.vscode`. Code is kept formatted and linted using `pylint`, `black` and `isort` with settings defined in `pyproject.toml`

## Architecture overview

This project uses [Scrapy](https://scrapy.org/) to obtain data from supported energy markets and [SQLAlchemy](https://www.sqlalchemy.org/) to store data, and [Alembic](https://alembic.sqlalchemy.org/en/latest/) for database migrations. Database storage has been tested with sqlite, postgres and mysql.

Overview of scrapy architecture:

![](https://docs.scrapy.org/en/latest/_images/scrapy_architecture_02.png)

## Code Navigation

* Spider definitions in `opennem/spiders`
* Processing pipelines for crawls in `opennem/pipelines`
* Database models for supported energy markets are stored in `opennem/db/models`
