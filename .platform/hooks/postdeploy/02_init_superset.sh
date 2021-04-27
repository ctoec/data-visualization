#!/bin/bash
cd ~

ADMIN_USERNAME="voldemort"
ADMIN_EMAIL="admin@ctoec.org"

SLEEP_COUNTER=0

# Give Superset container 5 minutes to start up before exiting early
until [ "`docker inspect -f {{.State.Running}} superset`"=="true" ] || [ $SLEEP_COUNTER -ge 60 ]; do
  echo "Superset container not up and running yet.  Still waiting..."
  SLEEP_COUNTER=$(( SLEEP_COUNTER + 1 ))
  sleep 5;
done;

if [ $SLEEP_COUNTER -ge 60 ];
then
  echo "Superset container wasn't started properly - initialization aborted."
  exit 1
fi

echo "Superset container available!  Starting initialization process..."

SUPERSET_ADMIN=$(docker exec superset superset fab list-users | grep $ADMIN_USERNAME | grep $ADMIN_EMAIL )

# If no Superset admin user has been created, assume this is a brand new application instance
# and perform all the necessary Superset initialization steps
if [ -z "$SUPERSET_ADMIN" ];
then
  echo "No Superset admin user found.  Continuing with intialization process..."

  echo "Upgrading Superset database..."
  docker exec superset superset db upgrade

  echo "Setting default Superset permissions..."
  docker exec superset superset init

  echo "Creating Superset admin user..."  
  STAGE=$(/opt/elasticbeanstalk/bin/get-config environment -k BUILD_ENV)
  PASSWORD=$(aws secretsmanager get-secret-value --secret-id /pensieve/$STAGE/superset/admin/password --query 'SecretString' --output text --region 'us-east-2')

  docker exec superset superset fab create-admin --username $ADMIN_USERNAME --firstname 'Admin' --lastname 'User' --email $ADMIN_EMAIL --password $PASSWORD

  echo "Superset initialization complete!"
else
  echo "Superset admin user has already been set up!  Skipping initialization..."
fi                                                                                                                                                                     