FROM kartoza/postgis:12.1 as base


RUN set -eux \
  && sh -c "echo 'deb https://packagecloud.io/timescale/timescaledb/debian/ `lsb_release -c -s` main' > /etc/apt/sources.list.d/timescaledb.list" \
  && wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | apt-key add - \
  && apt-get update \
  && apt-get  -y --no-install-recommends install timescaledb-2-postgresql-12 timescaledb-tools \
  && timescaledb-tune --quiet --yes \
  && apt-get -y --purge autoremove \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* \
  && echo "v2"

ADD infra/database/setup-timescale.sh /setup-timescale.sh
ADD infra/database/docker-entrypoint.sh /docker-entrypoint.sh
