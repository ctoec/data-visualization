import unittest
import pandas as pd
from sqlalchemy.sql import text
from pull_ece_data import get_mysql_connection, CHILD_SQL_FILE

MONTH = '2021-03-01'
DATA_ACTIVE_DATE = '2021-03-08'

class TestMatchingData(unittest.TestCase):

    # Call for data from DB once
    @classmethod    
    def setUpClass(cls):
        db_conn = get_mysql_connection(section='ECE Reporter DB')
        parameters = {'period': MONTH, 'active_data_date': DATA_ACTIVE_DATE}
        cls.month_child_df = pd.read_sql(sql=text(open(CHILD_SQL_FILE).read()),
                                         params=parameters,
                                         con=db_conn)

    def test_check_funding_and_enrollments(self):

        total_len = self.month_child_df.shape[0]
        duplicate_enrollments = total_len - self.month_child_df['enrollment_id'].nunique()
        duplicate_fundings = total_len - self.month_child_df['funding_id'].nunique()
        self.assertEqual(duplicate_fundings, 0)

        # Needs additional validation
        # assert duplicate_enrollments == 0

    def test_check_times(self):
        total_len = self.month_child_df.shape[0]
        self.assertEqual(sum(self.month_child_df.enrollment_exit <= pd.to_datetime(MONTH)),0)
        self.assertEqual((self.month_child_df.first_reporting_period <= self.month_child_df.reporting_period).sum(),total_len)


if __name__ == "__main__":
    unittest.main()