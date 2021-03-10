# OEC Data Visualization

### Superset creation from Dockerfile

The `docker` folder contains code to build an instance of Superset from a Dockerfile with a Postgres database attached.
The database will serve as the store of data for both metadata surrounding Superset chart creation and for enrollment data created in this repo.

In order to deploy locally two items need to be added to the `.env` file. CircleCI adds these lines in the deploy process. 

_Environmental Variables to Add to .env_
- MAPBOX_KEY
  - This is the API key that Superset uses to render maps, it is tied with Kyle Magida's email (kyle@skylight.digital)
  - This is stored in AWS Secrets Manager at `/data-viz/map_box/key`

### Superset config

This instance of Superset is configured with the file in `config/superset_config.py`. Additional configuration options can be found here: `https://github.com/apache/superset/blob/master/superset/config.py`

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
- ECE Reporter
  - Reports pulled from ECE reporter on a monthly basis
  - Initial backfill is also pulled
  - Data is extracted from ECE reporter and saved to a CSV.  
  - A config file with host, database, user and password named config.ini should be in the `ece_data` folder. A template 
  is provided in `ece_data/config_template.ini`.
  - _ECE Assumptions_    
    - Reporting period ids always increase as time increases
    - Family income determination should be the most recent entry by determination date for the family that is not deleted
    - For foster children, income should be set to 0 and family size should be 1.
    - The queries are made on temporal tables that return data as if the query was run against the database at the end of the given reporting period. Changes since that time will not be reflected in the results.
      - The end of the funding period for purposes of the timing of the snapshot will be the beginning of the next month
      - For backfilling data this approach does not work because data wasn't in the DB for some of these periods. March 8th 
      will be the date that is used in this case since it was the first deadline for data submission.  
  - C4K data is not included 
   
### Created tables

The clean_data script above will create two files in the `src/data_integration/july_2020/data` folder to be uploaded to Superset; 
`student_data.csv` populates the `uploaded_data.july_2020` table and `site_data.csv` populates the `uploaded_data.july_2020_sites` table. 


#### Reference data

- `fpl_and_smi.csv` is copied from data given to Skylight by OEC in 2020.
- `site_lat_long_lookup.json` is a json dictionary with a store of data collected from the Census API keyed with the called address.
  
### Data Visualization

The charts and layout for the dashboards is better stored in the [OEC POC Dashboard](http://ec2-3-134-85-99.us-east-2.compute.amazonaws.com/superset/dashboard/3/) directly. 
The SQL calculations that are behind the metrics are stored for reference and review here in `src/data_visualization`. 
Any changes to metrics or calculated columns should be accompanied by a pull request here to review the underlying SQL code.

A Mapbox API key is stored in AWS Secrets with key `/data-viz/map_box/key`. 

## Dashboard validation and deploy process

### Reviewing dashboard edits

Each set of dashboard edits should be tied with a ticket and reviewed and validated by other team members. The process will depend on whether the dashboard is published or unpublished.

Ideally, code changes, including the addition of new metrics, will be in separate tickets from dashboard edits to facilitate review and allow for divided responsibility.

#### Pre-production dashboards

Pre-production dashboards can be edited and reviewed directly before they are published. Once the team has determined the dashboard is ready to go live the dashboard itself can be set to published and it can be given a "slug" (name in the URL).
  
#### Production dashboards

Live production dashboards can be edited safely with the following process:

1. Make a full copy (including charts) of the existing production dashboard
1. Edit proposed new dashboard as needed, including using newly created metrics.
1. Submit dashboard for review to team for review and approval
1. Once changes are approved, publish dashboard by changing the "slug" to the production slug and removing the "slug" from the prior dashboard.
1. Legacy dashboard can be deleted once the new one is up. 
1. A new copy can then be made for future changes when needed.


### Editing and creating tables, metrics and columns

- Rather than editing, new metrics should be created first with new names
- Old metrics can be deleted in a subsequent review after it has been determined their removal will not affect production dashboards.
- The SQL associated with new metrics and calculated columns should be added to tables in Superset and reviewed there.
- Superset has an option for metrics for Certification and Certification Details that the writer can use.

#### Data Cleaning TODOS
- Fill outstanding lat, longs for sites
- Clean up town names
- Resolve outstanding student records that aren't matching to any sites

