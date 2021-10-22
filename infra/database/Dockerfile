# This container takes the kartoza/postgis as a base and installs timescaledb
# from source so that it can support multi-architecture builds.

# This is a multi-arch built version of kartoza/postgis
FROM nikc9/postgis:latest as base

# Install build requirements
ENV BUILD_PACKAGES="lsb-release git binutils vim libc6-dev patchutils gcc libc-dev make cmake libssl-dev devscripts equivs libkrb5-dev"
RUN set -eux \
  && export DEBIAN_FRONTEND=noninteractive \
  && apt-get -y update \
  && apt-get install -y ${BUILD_PACKAGES} \
  && apt-mark auto ${BUILD_PACKAGES}

# Create build environment
RUN mkdir -p /build \
  &&  chmod 777 /build

WORKDIR /build/

# Checkout the timescale repo. Supports passing tag as an argument.
# @TODO multi-version builds
ARG GITHUB_REPO=timescale/timescaledb
ARG GITHUB_TAG
RUN git clone "https://github.com/${GITHUB_REPO}" /build/timescaledb;

# Build timescaledb extension from source version
ARG TIMESCALE_VERSION=2.4.1
RUN cd /build/timescaledb \
  && git reset HEAD --hard \
  && git clean -f -d -x \
  && git checkout ${TIMESCALE_VERSION} \
  && rm -rf build \
  && PATH="/usr/lib/postgresql/${POSTGRES_MAJOR_VERSION}/bin:${PATH}" ./bootstrap -DTAP_CHECKS=OFF -DCMAKE_BUILD_TYPE=RelWithDebInfo -DREGRESS_CHECKS=OFF -DGENERATE_DOWNGRADE_SCRIPT=ON -DPROJECT_INSTALL_METHOD="${INSTALL_METHOD}"${OSS_ONLY} \
  && cd build \
  && make -j 6 install || exit 1;

RUN  echo $POSTGRES_MAJOR_VERSION >/tmp/pg_version.txt
RUN  echo $POSTGIS_MAJOR_VERSION >/tmp/pg_major_version.txt
RUN  echo $POSTGIS_MINOR_RELEASE >/tmp/pg_minor_version.txt

# Copy scripts
ADD infra/database/scripts /scripts
WORKDIR /scripts
RUN chmod +x *.sh
