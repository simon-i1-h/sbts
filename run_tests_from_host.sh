#!/bin/sh

set -e

CODEDIR=/home/app/opt/sbts
exec docker compose run --rm app gosu app "$CODEDIR/envw" python "$CODEDIR/manage.py" test "$CODEDIR/sbts"
