#!/usr/bin/env bash

set -e

# env vars for tuning
if [ -z "$POSTGRES_MAX_CONNECTIONS" ]; then
    POSTGRES_MAX_CONNECTIONS="300"
fi

if [ -z "$POSTGRES_SHARED_BUFFERS" ]; then
    POSTGRES_SHARED_BUFFERS="512MB"
fi

# backup conf file
cp $CONF{,.`date +"%Y%m%d_%H%M%S"`.bak}

# delete the keys we will put in optimisations
sed -i '/max_connections/d' $CONF

# write optimisations conf
cat > ${ROOT_CONF}/optimisations.conf <<EOF
max_connections = ${POSTGRES_MAX_CONNECTIONS}
shared_buffers = ${POSTGRES_SHARED_BUFFERS}
max_locks_per_transaction = 512
max_parallel_workers = 0
EOF


echo "include 'optimisations.conf'" >> $CONF
