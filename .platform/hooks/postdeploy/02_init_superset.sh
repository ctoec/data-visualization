#!/bin/bash
cd ~

if [ ! -f .superset-init ]; then
    SLEEP_COUNTER=0

    until [ "`docker inspect -f {{.State.Running}} superset`"=="true" ] || [ $SLEEP_COUNTER -ge 60 ]; do
      echo "Superset container not up and running yet.  Still waiting..."
      SLEEP_COUNTER=$(( SLEEP_COUNTER + 1 ))
      sleep 5;
    done;

    if [ $SLEEP_COUNTER -ge 60 ]; then
      echo "Superset container wasn't started properly - initialization aborted."
      exit 1
    fi

    echo "Superset container available!  Initialization started..."

    echo "Upgrading Superset database..."
    docker exec superset superset db upgrade

    echo "Setting default Superset permissions..."
    docker exec superset superset init

    echo "Creating Superset admin user..."  
    STAGE=$(/opt/elasticbeanstalk/bin/get-config environment -k BUILD_ENV)
    PASSWORD=$(aws secretsmanager get-secret-value --secret-id /pensieve/$STAGE/superset/admin/password --query 'SecretString' --output text --region 'us-east-2')

    docker exec superset superset fab create-admin --username 'voldemort' --firstname 'Admin' --lastname 'User' --email 'admin@ctoec.org' --password $PASSWORD

    touch .superset-init     
    echo "Superset initialization complete!"                                                                                                                                                                     
fi   