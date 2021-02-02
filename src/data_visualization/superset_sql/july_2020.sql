-- This file contains metrics that power charts in Superset, all Superset metrics should be logged here for review


-- Table july_2020

-- METRICS
-- Unique Students
count(DISTINCT("unique_name_ids"))

-- Percent of in-town students
count(DISTINCT unique_name_ids) filter (where attends_site_in_hometown) / count(DISTINCT unique_name_ids)::FLOAT

-- CALCULATED COLUMNS

-- Poverty Line
CASE WHEN "Annual Household Income" > federal_poverty_level THEN 'Over Poverty Line' ELSE 'Under Poverty Line' END

-- SMI Bucket
CASE WHEN "Annual Household Income" IS NULL THEN 'g. No Income Data'
     WHEN "Annual Household Income" > state_median_income * 1.5 THEN 'f. Over 150% SMI'
     WHEN "Annual Household Income" > state_median_income * 1 THEN 'e. Between 100% and 150% of SMI'
     WHEN "Annual Household Income" > state_median_income * .75 THEN 'd. Between 75% and 100% of SMI'
     WHEN "Annual Household Income" > state_median_income * .50 THEN 'c. Between 50% and 75% of SMI'
     WHEN "Annual Household Income" > state_median_income * .25 THEN 'b. Between 25% and 50% of SMI'
     ELSE 'a. Under 25% SMI'
     END

-- Age
DATE_PART('year',AGE(TO_DATE("Birth Month", 'YYYY-MM-DD')))::INT

-- Under 75% SMI
CASE
WHEN "Annual Household Income" IS NULL THEN 'No Income Data'
WHEN "Annual Household Income" > state_median_income * .75 THEN 'Over 75% SMI'
ELSE 'Under 75% SMI'
END