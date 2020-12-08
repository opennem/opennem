#!/usr/bin/env bash
prometheus --config.file=infra/prometheus/prometheus.yml --storage.tsdb.path=infra/prometheus/.data
