#!/bin/bash
REDIS_IP=$REDIS_SERVER_IP
if [ -z "$REDIS_SERVER_IP" ]
then
    REDIS_IP="localhost"
fi

echo "--> Running 'pip install'..."
pip install -r requirements/development.txt -r requirements/production.txt -r requirements/notebook.txt
echo "--> Connecting Redis server" $REDIS_SERVER_IP
echo "--> Flushing 'django compressor cache'..."
redis-cli -h $REDIS_IP KEYS ":1:django_compressor*" | xargs redis-cli -h $REDIS_IP DEL
echo "--> Running 'collect static'..."
python projectile/manage.py collectstatic --noinput --settings projectile.settings_live
echo "--> Running 'common release tag'..."
python projectile/manage.py common_release_tag --settings projectile.settings_live
echo "Done!"