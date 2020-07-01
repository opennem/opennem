#!/bin/bash
mkdir -p /app/logs

logparser -dir /app/logs -t 10 --delete_json_files &

exec $@