cd ../

# TODO: Do we need to copy this favicon like this?
docker cp images/favicon.ico superset:/app/superset/static/assets/images/favicon.png

if [ ! -f .initialized ]; then                                                                                                                                                                                    
    echo "Initializing database..."    

    docker exec -it superset superset db upgrade && docker exec -it superset superset init                 
    docker exec -it superset superset fab create-admin \
      --username USERNAME \
      --firstname FIRSTNAME \
      --lastname LASTNAME \
      --email EMAIL \
      --password ********

    touch .initialized                                                                                                                                                                                            
fi                                                                                                                                                                                                                

exec postgresql start