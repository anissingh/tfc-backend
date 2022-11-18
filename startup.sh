#!/usr/bin/env bash
python3 -m virtualenv venv
source venv/bin/activate
chmod +x startup.sh
chmod +x run.sh
chmod +x makepayments.sh
cd tfcbackend
pip install -r requirements.txt
chmod +x manage.py
./manage.py makemigrations
./manage.py migrate
export DJANGO_SUPERUSER_EMAIL='admin@gmail.com'
export DJANGO_SUPERUSER_PASSWORD='password'
./manage.py createsuperuser --noinput
cd ..
