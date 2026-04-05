#!/bin/sh
set -e

python manage.py migrate

if [ "${SEED_DB:-0}" = "1" ]; then
    python seed_db.py
fi

exec python manage.py runserver 0.0.0.0:8000
