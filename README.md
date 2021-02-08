# OEC Data Visualization

### Superset creation from Dockerfile

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
1. Add Database to store OEC data through Superset UI 
   - Add database through database UI with connection string `SQLALCHEMY_DATABASE_URI='postgresql+psycopg2://superset_admin:$SUPERSET_DB_PASS@superset_db/superset`
   - Enable CSV upload and all SQL Lab settings
1. Use SQL Lab to create uploaded_data schema
   - `CREATE SCHEMA uploaded_data;`
1. Load CSVs as needed 

### Data Sources

- July 2020 data
  - One time collection of data as of Feb. 2020
  - Stored in bucket referenced in [data retention policy.](https://docs.google.com/document/d/1fBBjWPdC9w8YUlCT47s9-G9jzy0vOQ9ejONviXkkCxI/edit#heading=h.3aiijg3fhho3)
  - Copy sheet `ECE Feb20 Data Collect_All_e` and paste as tab separated CSV (this should be the default) into `src/data_integration/july_2020/data/ece_feb_20_data_collection.csv`.
  - To clean data: go to `src/data_integration/july_2020/` and run `python3 clean_data.py` or `python clean_data.py` depending on your machine's binary for Python 3.

#### Reference data

- `fpl_and_smi.csv` is copied from data given to Skylight by OEC in 2020.
- `site_lat_long_lookup.json` is a json dictionary with a store of data collected from the Census API keyed with the called address.

 
### Created tables

The clean_data script above will create two files in the `src/data_integration/july_2020/data` folder that can be uploaded to Superset.
`student_data.csv` populates the `uploaded_data.july_2020` table and `site_data.csv` populates the `uploaded_data.july_2020_sites` table. 
  
### Data Visualization

The charts and layout for the dashboards is better stored in the [OEC POC Dashboard](http://ec2-3-134-85-99.us-east-2.compute.amazonaws.com/superset/dashboard/3/) directly. 
The SQL calculations that are behind the metrics are stored for reference and review here in `src/data_visualization`. 
Any changes to metrics or calculated columns should be accompanied by a pull request here to review the underlying SQL code.

A Mapbox API key is stored in AWS Secrets with key `/data-viz/map_box/key`. 


#### Data Cleaning TODOS
- Fill outstanding lat, longs for sites
- Clean up town names
- Resolve outstanding student records that aren't matching to any sites