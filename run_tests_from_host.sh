#!/bin/sh

set -eu

CODEDIR=/home/app/opt/sbts

if [ $# -eq 0 ]; then
  set -- "$CODEDIR/sbts"
fi

exec docker compose run --rm app gosu app "$CODEDIR/envw" python "$CODEDIR/manage.py" test "$@"
