import os
import configparser
import sqlalchemy

CONFIG_FILE = os.path.dirname(os.path.realpath(__file__)) + '/config.ini'

# Keys referring to configuration file
HOST_KEY = 'host'
DB_KEY = 'database'
USER_KEY = 'user'
PASSWORD_KEY = 'password'
PORT_KEY = 'port'
DB_TYPE_KEY = 'type'

POSTGRES = 'postgres'
SQL_SERVER = 'sql server'
VALID_DB_TYPES = [POSTGRES, SQL_SERVER]


def get_db_connection(section: str, config_file: str = CONFIG_FILE) -> sqlalchemy.engine.base.Connection:
    """
    Reads a configuration file, connects to the specified database and returns sqlalchemy engine
    :param section: section of configuration file that has DB creds
    :param config_file: path to configuration file
    :return engine: SQLAlchemy connection object
    """
    config = configparser.ConfigParser()
    config.read(config_file)

    # Get credentials from config file
    db_dict = config[section]
    host = db_dict[HOST_KEY]
    user_name = db_dict[USER_KEY]
    password = db_dict[PASSWORD_KEY]
    db_name = db_dict[DB_KEY]
    port = db_dict[PORT_KEY]
    db_type = db_dict[DB_TYPE_KEY]

    if db_type not in VALID_DB_TYPES:
        raise Exception(f"{db_type} is not a valid DB type, only {','.join(VALID_DB_TYPES)} are allowed.")

    if db_type == POSTGRES:
        conn_string = f'postgresql+psycopg2://{user_name}:{password}@{host}:{port}/{db_name}'
    elif db_type == SQL_SERVER:
        conn_string = f"mssql+pyodbc://{user_name}:{password}@{host},{port}/{db_name}?driver=ODBC+Driver+17+for+SQL+Server&Mars_Connection=Yes"
    # Create and return DB connection
    engine = sqlalchemy.create_engine(conn_string)
    conn = engine.connect()
    return conn
