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

echo "Upgrading Superset database..."
docker exec superset superset db upgrade

echo "Superset initialization complete!"