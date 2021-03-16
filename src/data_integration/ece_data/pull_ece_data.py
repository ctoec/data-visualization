import os
import sqlalchemy
import pandas as pd
import configparser
import calendar
from sqlalchemy.sql import text
from datetime import datetime

# File paths
DIR_NAME = os.path.dirname(os.path.realpath(__file__))
CHILD_SQL_FILE = DIR_NAME + '/child_pull.sql'
CONFIG_FILE = DIR_NAME + '/config.ini'

# Keys referring to configuration file
HOST_KEY = 'host'
DB_KEY = 'database'
USER_KEY = 'user'
PASSWORD_KEY = 'password'
PORT_KEY = 'port'

START_DATE = '2020-07-01'
END_DATE = '2021-02-01'
BACKFILL_DATA_ACTIVE_DATA = '2021-03-15'


def get_beginning_and_end_of_month(date: datetime.date) -> (datetime.date, datetime.date):
    """
    Get first and last day of a month
    :param date: date in a month to get the first and last date of
    :return: tuple of first and last day of a month
    """
    start = date.replace(day=1)
    end = date.replace(day=calendar.monthrange(date.year, date.month)[1])
    return start, end


def get_mysql_connection(section: str, config_file: str = CONFIG_FILE) -> sqlalchemy.engine.base.Connection:
    """
    Reads a configuration file, connects to the specified database and returns sqlalchemy engine
    :param section: section of configuration file that has DB creds
    :param config_file: path to configuration file
    :return engine: SQLAlchemy connection object
    """
    config = configparser.ConfigParser()
    config.read(config_file)

    # Get credentials from config file
    ece_db_dict = config[section]
    host = ece_db_dict[HOST_KEY]
    user_name = ece_db_dict[USER_KEY]
    password = ece_db_dict[PASSWORD_KEY]
    db_name = ece_db_dict[DB_KEY]
    port = ece_db_dict[PORT_KEY]

    # Create and return DB connection
    conn_string = f"mssql+pyodbc://{user_name}:{password}@{host},{port}/{db_name}?driver=ODBC+Driver+17+for+SQL+Server&Mars_Connection=Yes"
    engine = sqlalchemy.create_engine(conn_string)
    conn = engine.connect()
    return conn


def backfill_ece(db_conn: sqlalchemy.engine, start_month: str = START_DATE,
                 end_month: str = END_DATE, data_active_date: str = BACKFILL_DATA_ACTIVE_DATA) -> pd.DataFrame:
    """
    Pulls data from ECE Reporter for all the months between start and end month (inclusive) using data
    as of the data_active_date to adjust for data that was added in bulk after the relevant month
    :param db_conn: connection to ECE database
    :param start_month: First month to pull data from
    :param end_month: Last month to pull data from
    :param data_active_date: Date that will serve as the version point of the database pull. Data will be pulled from
    the database as if the query were run on this day.
    :return: Combined dataframe of all the months worth of data in the range
    """
    report_list = []
    for month in pd.date_range(start_month, end_month, freq='MS').tolist():
        print(f"Pulling {month}")
        parameters = {'period': month, 'active_data_date': data_active_date}
        month_child_df = pd.read_sql(sql=text(open(CHILD_SQL_FILE).read()), params=parameters, con=db_conn)
        report_list.append(month_child_df)
    final_df = pd.concat(report_list)
    return final_df


if __name__ == '__main__':
    ece_conn = get_mysql_connection(section='ECE Reporter DB')
    child_df = backfill_ece(ece_conn)
    child_df.to_csv('data/combined_data.csv', index=False)