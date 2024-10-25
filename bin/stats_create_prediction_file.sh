#!/bin/bash
source ~/env/bin/activate
cd ~/project

# Usage:
# */1 * * * * ~/project/bin/stats_create_prediction_file.sh live > ~/logs/cron.log 2>&1

python projectile/manage.py stats_create_prediction_file --settings=projectile.settings_$1