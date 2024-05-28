#!/bin/sh

# if any command failed in next command will fail whole script
set -e

python manage.py wait_for_db
python manage.py collectstatic --noinput
python manage.py migrate

# running uwsgi service
# --socket: running on PORT 9000
# --workers: running on 4 wsgi worker, usually depends on vCPU
# --master: running wsgi as daemon
# --eneble-threads: running for support multi-thread feature
# --module: entrypoint for uwsgi
uwsgi --socket :9000 --workers 4 --master --enable-threads --module app.wsgi