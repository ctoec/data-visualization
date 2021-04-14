if [ ! -f .initialized ]; then                                                                                                                                                                                    
    echo "Creating admin user..."  

    docker exec -it superset superset fab create-admin \
      --username 'voldemort' \
      --firstname 'ADMIN' \
      --lastname 'USER' \
      --email 'admin@ctoec.org' \
      --password 'password'

    touch .initialized                                                                                                                                                                                            
fi   