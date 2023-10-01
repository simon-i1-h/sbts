#!/usr/bin/env bash

set -eu

MINIO_ENDPOINT=http://minio:9000

doaws() {
  aws --endpoint-url "$MINIO_ENDPOINT" "$@"
}

# PostgreSQLが立ち上がるのを待つ
wait_pg() {
  for i in $(seq 0 4); do
    if psql service=sbts -c 'SELECT 1;' > /dev/null; then
      echo "$FUNCNAME: done"
      return 0
    fi

    echo 'sleep...'
    sleep $((2 ** i))
  done

  echo "$FUNCNAME: timed out" >&2
  return 1
}

# MinIOが立ち上がるのを待つ
wait_minio() {
  for i in $(seq 0 4); do
    if doaws s3 ls --page-size 1 > /dev/null; then
      echo "$FUNCNAME: done"
      return 0
    fi

    echo 'sleep...'
    sleep $((2 ** i))
  done

  echo "$FUNCNAME: timed out" >&2
  return 1
}

chown app:app /home/app/var
chown -R app:app /home/app/var/sbts
chown app:app /home/app/opt /home/app/opt/sbts
chown -R app:app /home/app/opt/sbts/config
cd /home/app/var/sbts

wait_pg
wait_minio

if ! doaws s3api head-bucket --bucket sbtsfile > /dev/null; then
  doaws s3 mb s3://sbtsfile
fi

MANAGEPY=/home/app/opt/sbts/manage.py

gosu app python "$MANAGEPY" migrate
exec gosu app python "$MANAGEPY" runserver 0.0.0.0:8000
