import os
import sqlalchemy
import pandas as pd
import calendar
from sqlalchemy.sql import text
from datetime import datetime

# File paths
DIR_NAME = os.path.dirname(os.path.realpath(__file__))
CHILD_SQL_FILE = DIR_NAME + '/child_pull.sql'
SPACE_SQL_FILE = DIR_NAME + '/space_pull.sql'
START_DATE = '2020-07-01'
END_DATE = '2021-03-01'


def get_space_df(db_conn: sqlalchemy.engine) -> pd.DataFrame:
    """
    Pulls capacity by organization
    :param db_conn: connection to run DB query
    :return: Dataframe of funding space table
    """
    df = pd.read_sql(sql=text(open(SPACE_SQL_FILE).read()), con=db_conn)
    return df


def backfill_ece(db_conn: sqlalchemy.engine, start_month: str = START_DATE, end_month: str = END_DATE) -> pd.DataFrame:
    """
    Pulls data from ECE Reporter for all the months between start and end month (inclusive) using data
    as of the data_active_date to adjust for data that was added in bulk after the relevant month
    :param db_conn: connection to ECE database
    :param start_month: First month to pull data from
    :param end_month: Last month to pull data from
    the database as if the query were run on this day.
    :return: Combined dataframe of all the months worth of data in the range
    """
    report_list = []
    for month in pd.date_range(start_month, end_month, freq='MS').tolist():
        print(f"Pulling {month}")
        parameters = {'period': month}
        month_child_df = pd.read_sql(sql=text(open(CHILD_SQL_FILE).read()), params=parameters, con=db_conn)
        report_list.append(month_child_df)
    final_df = pd.concat(report_list)
    return final_df
