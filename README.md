# OpenNEM Energy Market Data Access

![logo](https://developers.opennem.org.au/_static/logo.png)

**NOTE: This is the backend project** For the client python project see [opennem/opennempy](https://github.com/opennem/opennempy)

![Tests](https://github.com/opennem/opennem/workflows/Tests/badge.svg) [![codecov](https://codecov.io/gh/opennem/opennem/branch/master/graph/badge.svg?token=HSJP632WBX)](https://codecov.io/gh/opennem/opennem)

The OpenNEM project aims to make the wealth of public National Electricity Market (NEM) data more accessible to a wider audience.

This toolkit enables downloading, mirroring and accessing energy data from various networks

Project homepage at https://opennem.org.au

Available on Docker at https://hub.docker.com/r/opennem/opennem

Currently supports:

- Australian NEM: https://www.nemweb.com.au/
- West Australia Energy Market: http://data.wa.aemo.com.au/

## Requirements

 * Python 3.10+ (see `.python-version` with `pyenv`)
 * Docker and `docker-compose` if you want to run the local dev stack

## Local Development Environment

Start the local docker stack

```sh
$ docker-compose up -d
```

## Quickstart

With poetry:

```sh
$ poetry install
$ poetry shell
$ alembic upgrade head
$ ./scripts/init.py
```

With pip + venv:

```sh
$ python -m venv .venv
$ pip install -r requirements.txt
$ source .venv/bin/activate
$ alembic upgrade head
$ ./scripts/init.py
```

## Initialization

The init script will setup all facilities from the latest `stations.json` file - crawl the last 7 days of data and run all the aggregate methods required for output.


## Usage

List the crawlers

```sh
$ opennem crawl list
```

Crawl

```sh
$ opennem crawl run au.nem.current.dispatch_scada
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

The `opennem` cli interface provides other options and settings:

```sh
$ opennem -h
```

Settings for Visual Studio Code are stored in `.vscode`. Code is kept formatted and linted using `pylint`, `black` and `isort` with settings defined in `pyproject.toml`

[Pre-commit](https://pre-commit.com/) hooks run before every commit. To setup:

```
$ pre-commit install
```

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

## Code Navigation

* Database models for supported energy markets are stored in `opennem/db/models`
* API intercace at `opennem/api`

# Notebooks

The OpenNEM project is packaged with a number of example Jupyter notebooks demonstrating use of the API and library. The dependancies to run notebooks are found in `requirements_notebooks.txt` in the root folder. The example notebooks are contained in `notebooks` and there is a configured Jupyter profile in `.jupyter`.

To set it up first install the requirements, and then start the Jupyter server

```sh
$ source .venv/bin/activate
$ pip install -r requirements_notebooks.txt
$ jupyter notebook
```
