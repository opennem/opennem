# OpenNEM Energy Market Data Access

The OpenNEM project aims to make the wealth of public National Electricity Market (NEM) data more accessible to a wider audience.

This toolkit enables downloading, mirroring and accessing energy data from various networks

Project homepage at https://opennem.org.au

Available on Docker at https://hub.docker.com/r/opennem/opennem

Currently supports:

- Australian NEM: https://www.nemweb.com.au/
- West Australia Energy Market: http://data.wa.aemo.com.au/

## Requirements

 * Python 3.7+ (see `.python-version` with `pyenv`)
 * Docker and `docker-compose` if you want to run the local dev stack

## Quickstart

With poetry:

```sh
$ poetry install
$ source .venv/bin/activate
$ ./init.sh
```

With pip + venv:

```sh
$ pip -m venv .venv
$ pip install -r requirements.txt
$ source .venv/bin/activate
$ ./init.sh
```

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

## Install Extras

The package contains extra modules that can be installed:

```sh
$ poetry install -E postgres
```

The list of extras are:

 * `postgres` - Postgres database drivers
 * `server` - API server

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

This project uses the new `pyproject.toml` project and build specification file. To make use of it use the `poetry` tool which can be installed on Windows, MacOS and Linux:

https://python-poetry.org/docs/

Installation instructions for Poetry are at:

https://python-poetry.org/docs/#installation

By default poetry will install virtual environments in your home metadata directory. A good alternative is to install the `venv` locally for each project with the following setting:

```sh
$ poetry config virtualenvs.in-project true
```

This will create the virtual environment within the project folder in a folder called `.venv`. This folder is ignored by git by default.

Setting up a virtual environment and installing requiements using Poetry:

```sh
$ poetry install
```

To activate the virtual environment either run:

```sh
$ poetry shell
```

Or you can just activate the standard `venv`

```sh
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

## Testing

Tests are in `tests/`

Run tests with:

```sh
$ pytest
```

Run background test watcher with

```sh
$ ptw
```

## Build Release

The script `build-release.sh` will tag a new release, build the docker image, tag the git version, push to GitHub and push the latest
release to PyPi


## Architecture overview

This project uses [Scrapy](https://scrapy.org/) to obtain data from supported energy markets and [SQLAlchemy](https://www.sqlalchemy.org/) to store data, and [Alembic](https://alembic.sqlalchemy.org/en/latest/) for database migrations. Database storage has been tested with sqlite, postgres and mysql.

Overview of scrapy architecture:

![](https://docs.scrapy.org/en/latest/_images/scrapy_architecture_02.png)

## Code Navigation

* Spider definitions in `opennem/spiders`
* Processing pipelines for crawls in `opennem/pipelines`
* Database models for supported energy markets are stored in `opennem/db/models`

## Deploy Crawlers

You can deploy the crawlers to the scrapyd server with:

```sh
$ scrapyd-deploy
```

If you don't have that command and it isn't available install it with:

```sh
$ pip install scrapyd-client
```

Which installs the [scrapyd-client](https://github.com/scrapy/scrapyd-client) tools. Project settings are read from `scrapy.cfg`
