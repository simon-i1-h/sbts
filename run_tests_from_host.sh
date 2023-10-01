#!/bin/sh

set -eu

if [ $# -eq 0 ]; then
  set -- sbts
fi

CODEDIR=/home/app/opt/sbts
exec docker compose run --rm app gosu app "$CODEDIR/envw" python "$CODEDIR/manage.py" test "$@"
