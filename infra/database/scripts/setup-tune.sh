#!/usr/bin/env bash

set -e

source /scripts/env-data.sh

# env vars for tuning
if [ -z "$POSTGRES_MAX_CONNECTIONS" ]; then
    POSTGRES_MAX_CONNECTIONS="300"
fi

# backup conf file
cp $CONF{,.`date +"%Y%m%d_%H%M%S"`.bak}

# delete the keys we will put in optimisations
sed -i '/max_connections/d' $CONF

# write optimisations conf
cat > ${ROOT_CONF}/optimisations.conf <<EOF
max_connections = ${POSTGRES_MAX_CONNECTIONS}

EOF
echo "include 'optimisations.conf'" >> $CONF
fi
