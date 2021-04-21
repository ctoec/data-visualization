#!/bin/bash
cd ~

if [ ! -f .superset-init ]; then
    echo "Setting default Superset permissions..."
    docker exec -it superset superset init

    echo "Creating Superset admin user..."  
    docker exec -it superset superset fab create-admin \
      --username 'voldemort' \
      --firstname 'ADMIN' \
      --lastname 'USER' \
      --email 'admin@ctoec.org' \
      --password 'password'

    touch .superset-init     
    echo "Superset initialization complete!"                                                                                                                                                                     
fi   