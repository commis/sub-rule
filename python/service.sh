#!/bin/bash

set -e

basepath=$(
  cd "$(dirname "$0")" || exit 1
  pwd
)

#cd "${basepath}/python" || exit 1
gunicorn -w 2 -b 0.0.0.0:5000 flash_app:app
