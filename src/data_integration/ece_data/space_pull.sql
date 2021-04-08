SELECT id as funding_space_id,
       source as funding_source,
       ageGroup as funding_space_age_group,
       time as funding_space_time,
       organizationId as organization_id,
       CASE capacity WHEN -1 THEN null else capacity END
FROM funding_space
-- Only CDC and Smart Start currently have valid capacity numbers. Once we have a system for collecting
-- School Readiness data those funding streams can be included
WHERE source IN ('CDC', 'SS')
