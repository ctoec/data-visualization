create table uploaded_data.ct_town_geo
(
	name text,
	state_id text,
	county_id text,
	town_id text,
	geo_id text,
	lat double precision,
	long double precision,
	geometry text
);

create table uploaded_data.ct_house_geo
(
	state_id text,
	house_district_id text,
	geo_id text,
	legislator_name text,
	legislator_party text,
	lat double precision,
	long double precision,
	geometry text
);

create table uploaded_data.ct_senate_geo
(
	state_id text,
	senate_district_id text,
	geo_id text,
	legislator_name text,
	legislator_party text,
	lat double precision,
	long double precision,
	geometry text
);
