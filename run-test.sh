#!/bin/bash

if [ "$1" ];
    then
    if [ "$2" ] && [[ $2 == ?(-)+([0-9]) ]];
        then
        for ind in $(seq 1 $2)
        do
            if [[ $ind > 1 ]];
                then echo $'\n\n******************************************************\n\n'
            fi
            echo "--> Running $ind times test for" $1 "...."
            python projectile/manage.py test -n $1
        done
    else
        echo "--> Running test for" $* "...."
        python projectile/manage.py test -n $*
    fi
else
    echo "--> Running 'test for omis'..."
    python projectile/manage.py test -n projectile
fi
echo "Done!"
