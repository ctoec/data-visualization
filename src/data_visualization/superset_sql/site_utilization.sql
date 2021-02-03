-- Creation Script
select site."Site Name",
       site."Full Address",
       site."Preschool Spaces",
       site."Infant/Toddler Spaces",
       site."School Age Spaces",
       site."All Available Spaces",
       site."Facility Code",
       site."Town Code",
       site."Address",
       site."Town",
       site."ZIP Code",
       site."Latitude",
       site."Longitude",
       site."Town from Census",
       count(DISTINCT student.unique_name_ids) as enrolled_students
FROM uploaded_data.july_2020 as student
INNER JOIN uploaded_data.july_2020_sites as site on student."ECIS/PSIS Facility Code" = TRIM(LEADING '0' FROM site."Facility Code")
GROUP BY
       site."Site Name",
       site."Full Address",
       site."Preschool Spaces",
       site."Infant/Toddler Spaces",
       site."School Age Spaces",
       site."All Available Spaces",
       site."Facility Code",
       site."Town Code",
       site."Address",
       site."Town",
       site."ZIP Code",
       site."Latitude",
       site."Longitude",
       site."Town from Census"