#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")"
zstd --ultra -20 -T0 --progress -v --rm fake_cache_data.json
