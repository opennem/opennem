FROM kartoza/postgis:12.4 as base


RUN set -eux \
  && sh -c "echo 'deb https://packagecloud.io/timescale/timescaledb/debian/ `lsb_release -c -s` main' > /etc/apt/sources.list.d/timescaledb.list" \
  && wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | apt-key add - \
  && apt-get update \
  && apt-get  -y --no-install-recommends install timescaledb-2-postgresql-12 timescaledb-tools postgresql-12-periods \
  && timescaledb-tune --quiet --yes \
  && apt-get -y --purge autoremove \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* \
  && echo "v3"

RUN  echo $POSTGRES_MAJOR_VERSION >/tmp/pg_version.txt
RUN  echo $POSTGIS_MAJOR_VERSION >/tmp/pg_major_version.txt
RUN  echo $POSTGIS_MINOR_RELEASE >/tmp/pg_minor_version.txt

# Copy scripts
ADD infra/database/scripts /scripts
WORKDIR /scripts
RUN chmod +x *.sh
