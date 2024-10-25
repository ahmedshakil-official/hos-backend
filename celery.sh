#!/bin/bash

# if [ "$1" ]; then
#     echo "--> Running Celery in Development mode...."
#    python projectile/manage.py celery worker
# else
#     echo "--> Running Celery in Development mode With auto reload..."
#    python projectile/manage.py celery_service
# fi

echo "--> Running Celery in Development mode...."
cd projectile && celery -A projectile worker -l info