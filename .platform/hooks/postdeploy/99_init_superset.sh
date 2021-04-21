#!/bin/bash
cd ~

if [ ! -f .superset-init ]; then
    echo "Setting default Superset permissions..."
    docker exec -it superset superset init

    echo "Creating Superset admin user..."  
    STAGE=$(/opt/elasticbeanstalk/bin/get-config environment -k BUILD_ENV)
    PASSWORD=$(aws secretsmanager get-secret-value --secret-id /pensieve/$STAGE/superset/admin/password --query 'SecretString' --output text --region 'us-east-2')

    docker exec -it superset superset fab create-admin \
      --username 'voldemort' \
      --firstname 'Admin' \
      --lastname 'User' \
      --email 'admin@ctoec.org' \
      --password $PASSWORD

    touch .superset-init     
    echo "Superset initialization complete!"                                                                                                                                                                     
fi   