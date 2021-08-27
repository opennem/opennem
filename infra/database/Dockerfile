FROM nikc9/postgis:latest as base

# setup build environment
ENV BUILD_PACKAGES="lsb-release git binutils libc6-dev patchutils gcc libc-dev make cmake libssl-dev devscripts equivs libkrb5-dev"
RUN apt-get -y update \
  && apt-get install -y ${BUILD_PACKAGES} \
  && apt-mark auto ${BUILD_PACKAGES}

RUN mkdir -p /build
RUN chmod 777 /build
WORKDIR /build/

# checkout
ARG GITHUB_REPO=timescale/timescaledb
ARG GITHUB_TAG
RUN git clone "https://github.com/${GITHUB_REPO}" /build/timescaledb;

# build TS version
ARG TIMESCALE_VERSION=2.4.1
RUN cd /build/timescaledb && git reset HEAD --hard && git clean -f -d -x && git checkout ${TIMESCALE_VERSION} \
  && rm -rf build \
  && PATH="/usr/lib/postgresql/${POSTGRES_MAJOR_VERSION}/bin:${PATH}" ./bootstrap -DTAP_CHECKS=OFF -DCMAKE_BUILD_TYPE=RelWithDebInfo -DREGRESS_CHECKS=OFF -DGENERATE_DOWNGRADE_SCRIPT=ON -DPROJECT_INSTALL_METHOD="${INSTALL_METHOD}"${OSS_ONLY} \
  && cd build && make -j 6 install || exit 1;

RUN  echo $POSTGRES_MAJOR_VERSION >/tmp/pg_version.txt
RUN  echo $POSTGIS_MAJOR_VERSION >/tmp/pg_major_version.txt
RUN  echo $POSTGIS_MINOR_RELEASE >/tmp/pg_minor_version.txt

# Copy scripts
ADD infra/database/scripts /scripts
WORKDIR /scripts
RUN chmod +x *.sh
