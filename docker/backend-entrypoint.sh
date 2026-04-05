#!/bin/sh
set -e

python manage.py migrate

SEED_MODE="${SEED_DB:-auto}"

if [ "$SEED_MODE" = "1" ]; then
    python seed_db.py
elif [ "$SEED_MODE" = "auto" ]; then
    if python manage.py shell -c "from django.contrib.auth.models import User; import sys; sys.exit(0 if User.objects.exists() else 1)"; then
        echo "Seed skipped: users already exist."
    else
        echo "Seed started: database is empty."
        python seed_db.py
    fi
fi

exec python manage.py runserver 0.0.0.0:8000
