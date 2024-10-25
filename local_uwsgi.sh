#!/bin/bash
echo "--> Running Project using UWSGI"
cd projectile && uwsgi --http :8000 --wsgi-file projectile/wsgi.py