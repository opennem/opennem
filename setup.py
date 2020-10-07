# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['opennem',
 'opennem.agent',
 'opennem.api',
 'opennem.api.admin',
 'opennem.api.facility',
 'opennem.api.photo',
 'opennem.api.revision',
 'opennem.api.station',
 'opennem.api.stats',
 'opennem.api.weather',
 'opennem.commands',
 'opennem.controllers',
 'opennem.core',
 'opennem.core.facility',
 'opennem.core.stations',
 'opennem.core.unit',
 'opennem.datetimes',
 'opennem.db',
 'opennem.db.migrations',
 'opennem.db.migrations.versions',
 'opennem.db.models',
 'opennem.diff',
 'opennem.exporter',
 'opennem.geo',
 'opennem.importer',
 'opennem.nem_derived',
 'opennem.pipelines',
 'opennem.pipelines.aemo',
 'opennem.pipelines.aemo.mms',
 'opennem.pipelines.nem',
 'opennem.pipelines.wem',
 'opennem.scheduler',
 'opennem.schema',
 'opennem.settings',
 'opennem.spiders',
 'opennem.spiders.aemo',
 'opennem.spiders.bom',
 'opennem.spiders.nem',
 'opennem.spiders.wem',
 'opennem.utils']

package_data = \
{'': ['*'],
 'opennem': ['data/*'],
 'opennem.core': ['data/*'],
 'opennem.db': ['fixtures/*', 'views/*']}

install_requires = \
['Wikidata>=0.7.0,<0.8.0',
 'alembic>=1.4.2,<2.0.0',
 'click>=7.1.2,<8.0.0',
 'dictalchemy>=0.1.2,<0.2.0',
 'dictdiffer>=0.8.1,<0.9.0',
 'geoalchemy2>=0.8.4,<0.9.0',
 'geojson>=2.5.0,<3.0.0',
 'huey>=2.2.0,<3.0.0',
 'mdutils>=1.3.0,<2.0.0',
 'openpyxl>=3.0.4,<4.0.0',
 'pillow>=7.2.0,<8.0.0',
 'pydantic>=1.5.1,<2.0.0',
 'python-dateutil>=2.8.1,<3.0.0',
 'python-dotenv>=0.14.0,<0.15.0',
 'pytz>=2020.1,<2021.0',
 'pyyaml>=5.3.1,<6.0.0',
 'redis>=3.5.3,<4.0.0',
 'requests>=2.23.0,<3.0.0',
 'requests_cache>=0.5.2,<0.6.0',
 'scrapy>=2.1.0,<3.0.0',
 'sentry-sdk>=0.14.4,<0.15.0',
 'shapely>=1.7.0,<2.0.0',
 'smart_open>=2.0.0,<3.0.0',
 'sqlalchemy>=1.3.17,<2.0.0',
 'ujson>=3.1.0,<4.0.0',
 'wikipedia>=1.4.0,<2.0.0']

extras_require = \
{'postgres': ['psycopg2-binary>=2.8.5,<3.0.0'],
 'server': ['uvicorn>=0.11.7,<0.12.0', 'fastapi[all]>=0.60.1,<0.61.0']}

entry_points = \
{'console_scripts': ['opennem = opennem.cli:main']}

setup_kwargs = {
    'name': 'opennem',
    'version': '3.0.0a22',
    'description': 'opennem engine agent',
    'long_description': "# OpenNEM Energy Market Data Access\n\nThe OpenNEM project aims to make the wealth of public National Electricity Market (NEM) data more accessible to a wider audience.\n\nThis toolkit enables downloading, mirroring and accessing energy data from various networks\n\nProject homepage at https://opennem.org.au\n\nAvailable on Docker at https://hub.docker.com/r/opennem/opennem\n\nCurrently supports:\n\n- Australian NEM: https://www.nemweb.com.au/\n- West Australia Energy Market: http://data.wa.aemo.com.au/\n\n\n## Install\n\nYou can install this project with python `pip`:\n\n```sh\n$ pip install opennem\n```\n\nOr alternatively with docker:\n\n```\n$ docker pull opennem/opennem\n```\n\nBundled with sqlite support. Other database drivers are optional and not installed by default. Install a supported database driver:\n\nPostgres:\n\n```sh\n$ pip install psycopg2\n```\n\n## Install Extras\n\nThe package contains extra modules that can be installed:\n\n```sh\n$ poetry install -E postgres\n```\n\nThe list of extras are:\n\n * `postgres` - Postgres database drivers\n * `server` - API server\n\n## Usage\n\nList the crawlers\n\n```sh\n$ scrapy list\n```\n\nCrawl\n\n```sh\n$ scrapy crawl au.nem.current.dispatch_scada\n```\n\n## Development\n\nThis project uses the new `pyproject.toml` project and build specification file. To make use of it use the `poetry` tool which can be installed on Windows, MacOS and Linux:\n\nhttps://python-poetry.org/docs/\n\nInstallation instructions for Poetry are at:\n\nhttps://python-poetry.org/docs/#installation\n\nBy default poetry will install virtual environments in your home metadata directory. A good alternative is to install the `venv` locally for each project with the following setting:\n\n```sh\n$ poetry config virtualenvs.in-project true\n```\n\nThis will create the virtual environment within the project folder in a folder called `.venv`. This folder is ignored by git by default.\n\nSetting up a virtual environment and installing requiements using Poetry:\n\n```sh\n$ poetry install\n```\n\nTo activate the virtual environment either run:\n\n```sh\n$ poetry shell\n```\n\nOr you can just activate the standard `venv`\n\n```sh\n$ source .venv/bin/activate\n```\n\nSettings are read from environment variables. Environment variables can be read from a `.env` file in the root of the folder. Setup the environment by copying the `.env.sample` file to `.env`. The defaults in the sample file map to the settings in `docker-compose.yml`\n\nThere is a `docker-compose` file that will bring a local database:\n\n```sh\n$ docker-compose up -d\n```\n\nCreate PostgreSQL databases\n\n```sh\npsql --username $POSTGRES_USER <<EOF\nCREATE DATABASE opennem;\nCREATE DATABASE opennem_dev;\nEOF\n```\n\nStart using alembic create the versions directory\n\n```sh\n$ mkdir opennem/db/migrations/versions\n```\n\nBring up the database migrations using alembic:\n\n```sh\n$ alembic upgrade head\n```\n\nRun scrapy in the root folder for options:\n\n```sh\n$ scrapy\n```\n\nThe `opennem` cli interface provides other options and settings:\n\n```sh\n$ opennem --help\n```\n\nSettings for Visual Studio Code are stored in `.vscode`. Code is kept formatted and linted using `pylint`, `black` and `isort` with settings defined in `pyproject.toml`\n\n## Testing\n\nTests are in `tests/`\n\nRun tests with:\n\n```sh\n$ pytest\n```\n\nRun background test watcher with\n\n```sh\n$ ptw\n```\n\n## Build Release\n\nThe script `build-release.sh` will tag a new release, build the docker image, tag the git version, push to GitHub and push the latest\nrelease to PyPi\n\n\n## Architecture overview\n\nThis project uses [Scrapy](https://scrapy.org/) to obtain data from supported energy markets and [SQLAlchemy](https://www.sqlalchemy.org/) to store data, and [Alembic](https://alembic.sqlalchemy.org/en/latest/) for database migrations. Database storage has been tested with sqlite, postgres and mysql.\n\nOverview of scrapy architecture:\n\n![](https://docs.scrapy.org/en/latest/_images/scrapy_architecture_02.png)\n\n## Code Navigation\n\n* Spider definitions in `opennem/spiders`\n* Processing pipelines for crawls in `opennem/pipelines`\n* Database models for supported energy markets are stored in `opennem/db/models`\n\n## Deploy Crawlers\n\nYou can deploy the crawlers to the scrapyd server with:\n\n```sh\n$ scrapyd-deploy\n```\n\nIf you don't have that command and it isn't available install it with:\n\n```sh\n$ pip install scrapyd-client\n```\n\nWhich installs the [scrapyd-client](https://github.com/scrapy/scrapyd-client) tools. Project settings are read from `scrapy.cfg`\n",
    'author': 'Dylan McConnell',
    'author_email': 'dylan.mcconnell@unimelb.edu.au',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://opennem.org.au',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'extras_require': extras_require,
    'entry_points': entry_points,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)

# This setup.py was autogenerated using poetry.
