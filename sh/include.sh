#!/bin/bash

PROJECT_ROOT=

if [ -z "$PROJECT_ROOT" ]; then
    echo "PROJECT_ROOT not defined"
    exit 1
fi

DATA_DIR="$PROJECT_ROOT/data"
CACHE_DIR="$PROJECT_ROOT/data/cache"

[ -d "${CACHE_DIR}" ] || mkdir -p "${CACHE_DIR}"
