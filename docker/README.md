# Superset creation from Dockerfile

This folder contains code to build an instance of Superset from a Dockfile with a Postgres database attached.
The database will serve as the store of data for both metadata surrounding Superset chart creation and for enrollment data created in this repo.

### Superset config

This instance of Superset is configured with the file in `config/superset_config.py`. Additional configuration options can be found here: `https://github.com/apache/superset/blob/master/superset/config.py`

The CircleCI process adds the following line `SQLALCHEMY_DATABASE_URI='postgresql+psycopg2://superset_admin:$SUPERSET_DB_PASS@superset_db/superset` to the file to set up the deployed Postgres instance as the database for the Superset metadata.

### Enrollment data

Data used in charts for this instance of Superset will be uploaded manually through the Superset UI and stored in the uploaded_data schema of the postgres database.
This data includes:
- `src/data_integration/july_2020/data/stripped_file` named as table july_2020 in the database.

### Initial Database Setup
 
When the database is initially built it needs to be set up with the following steps:

1. Upgrade and initialize database from command line of Superset instance
   - `docker exec -it superset superset db upgrade && docker exec -it superset superset init`
1. Create admin user from command line of Superset instance
   - `docker exec -it superset superset fab create-admin \
                 --username USERNAME \
                --firstname FIRSTNAME \
                --email EMAIL \
                --password ********`
1. Add Database to Superset UI
   - Add database through database UI with connection string `SQLALCHEMY_DATABASE_URI='postgresql+psycopg2://superset_admin:$SUPERSET_DB_PASS@superset_db/superset`
   - Enable CSV upload and all SQL Lab settings
1. Use SQL Lab to create uploaded_data schema
   - `CREATE SCHEMA uploaded_data;`
1. Load CSVs as needed 
                