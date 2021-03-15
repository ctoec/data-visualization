select
    convert(nvarchar(100), child.Id) as source_child_id,
    f.Id as funding_id,
    organization.Id as organization_id,
    organization.providerName as organization_name,
    site.Id as site_id,
    site.siteName as site_name,
    site.facilityCode as facility_code,
    site.region as site_region,
    site.titleI,
    site.licenseNumber as site_license_number,
    enrollment.id as enrollment_id,
    family_det_temp.family_determination_id,
    family.Id as family_id,
    rp.period as reporting_period,
    rp.periodStart as reporting_period_start,
    rp.periodEnd as reporting_period_end,
    CASE WHEN child.sasid is NULL then 0 ELSE 1 END as has_sasid,
       fs.id as funding_space_id,
       rp_first.period as first_reporting_period,
       rp_last.period as last_reporting_period,
       family_det_temp.family_determination_id as family_det_id,
      -- These can be added in as needed, PII is not needed for current iterations
--     child.lastName as last_name,
--     child.middleName as middle_name,
--     child.firstName as first_name,
--     child.birthCertificateId as birth_certificate_id,
--     family.streetAddress as family_street_address,
--     child.sasid,
    DATEADD(DAY, 1 ,EOMONTH(child.birthdate, -1)) as birth_month,
    CASE WHEN child.birthState = 'CT' THEN 1
         ELSE 0
         END as is_born_in_ct,
    child.foster,
    child.americanIndianOrAlaskaNative as american_indian_or_alaska_native,
	child.asian,
	child.blackOrAfricanAmerican as black_or_african_american,
	child.nativeHawaiianOrPacificIslander as native_hawaiian_or_pacific_islander,
	child.white,
	child.hispanicOrLatinxEthnicity as hispanic_or_latinx_ethnicity,
	child.gender,
    child.dualLanguageLearner as dual_language_learner,
    child.receivesDisabilityServices as recieves_disability_services,
    family.id as family_id,
    family.town as family_town,
    family.state as family_state,
    family.zipCode as family_zip_code,
    family.homelessness as family_homelessness,
    fs.time as funding_space_time,
    fs.ageGroup as funding_space_age_group,
    fs.source as funding_source,
    enrollment.ageGroup as enrollment_age_group,
    enrollment.entry as enrollment_entry,
    enrollment.[exit] as enrollment_exit,
    CASE WHEN child.foster = 'Yes' THEN 1
         ELSE family_det_temp.numberOfPeople
         END as family_size,
    CASE WHEN child.foster = 'Yes' THEN 0
         ELSE family_det_temp.income
         END as family_income,
    family_det_temp.incomeNotDisclosed as family_income_not_disclosed
    from dbo.funding
        FOR SYSTEM_TIME AS OF :active_data_date as f
    inner join dbo.funding_space
        FOR SYSTEM_TIME AS OF :active_data_date as fs on f.fundingSpaceId = fs.id
    inner join dbo.reporting_period as rp_first on f.firstReportingPeriodId = rp_first.id and fs.source = rp_first.type
    inner join dbo.reporting_period as rp on fs.source = rp.type and rp.period = :period
    left outer join dbo.reporting_period as rp_last on f.lastReportingPeriodId = rp_last.ID and fs.source = rp_last.type
    inner join dbo.enrollment
        FOR SYSTEM_TIME AS OF :active_data_date as enrollment on enrollment.Id = f.enrollmentId and
                                                            (enrollment.[exit] is null or enrollment.[exit] > rp.periodStart)
    inner join dbo.site
        FOR SYSTEM_TIME AS OF :active_data_date as site on site.Id = enrollment.siteId
    inner join dbo.organization
        FOR SYSTEM_TIME AS OF :active_data_date as organization on site.organizationId = organization.Id
    inner join dbo.child
        FOR SYSTEM_TIME AS OF :active_data_date as child ON child.Id = enrollment.childId
    inner join dbo.family
        FOR SYSTEM_TIME AS OF :active_data_date AS family on child.familyId = family.id
    left join (
        select
          id as family_determination_id,
          familyId,
          income,
          numberOfPeople,
          incomeNotDisclosed,

          row_number() over (
            partition by familyId
            order by determinationDate desc
          ) as rn

        from dbo.income_determination
         FOR SYSTEM_TIME AS OF :active_data_date
         where deletedDate is null) as family_det_temp
      on family_det_temp.familyId = family.Id and rn = 1
where rp_first.period <= :period and (rp_last.period is null or rp_last.period >= :period)
AND f.deletedDate is NULL AND
    enrollment.deletedDate IS NULL and
    child.deletedDate is NULL and
    family.deletedDate is NULL

