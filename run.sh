#!/usr/bin/env bash
source venv/bin/activate
cd tfcbackend
echo "Enter port for server to run on"
read PORT
./manage.py runserver $PORT
