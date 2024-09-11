# Database Schema

Database: opennem
PostgreSQL version: PostgreSQL 16.4 (Ubuntu 16.4-1.pgdg22.04+1) on x86_64-pc-linux-gnu, compiled by gcc (Ubuntu 11.4.0-1ubuntu1~22.04) 11.4.0, 64-bit

## Table of Contents

| Table Name | Row Count |
|------------|----------|
| [aemo_facility_data](#aemo-facility-data) | 0 |
| [aemo_market_notices](#aemo-market-notices) | 815 |
| [alembic_version](#alembic-version) | 1 |
| [api_keys](#api-keys) | 1 |
| [at_facility_daily](#at-facility-daily) | 2,885,368 |
| [at_network_demand](#at-network-demand) | 62,753 |
| [at_network_flows](#at-network-flows) | 7,917,760 |
| [at_network_flows_v3](#at-network-flows-v3) | 0 |
| [balancing_summary](#balancing-summary) | 11,323,660 |
| [bom_observation](#bom-observation) | 5,920,234 |
| [bom_station](#bom-station) | 773 |
| [crawl_history](#crawl-history) | 788,303 |
| [crawl_meta](#crawl-meta) | 50 |
| [facility](#facility) | 787 |
| [facility_scada](#facility-scada) | 769,216,886 |
| [facility_status](#facility-status) | 12 |
| [feedback](#feedback) | 94 |
| [fueltech](#fueltech) | 26 |
| [fueltech_group](#fueltech-group) | 10 |
| [geography_columns](#geography-columns) | 0 |
| [geometry_columns](#geometry-columns) | 3 |
| [location](#location) | 551 |
| [milestones](#milestones) | 15,148 |
| [mv_fueltech_daily](#mv-fueltech-daily) | 361,037 |
| [mv_weather_observations](#mv-weather-observations) | 5,409,699 |
| [network](#network) | 7 |
| [network_region](#network-region) | 12 |
| [participant](#participant) | 201 |
| [pg_stat_statements](#pg-stat-statements) | 152 |
| [pg_stat_statements_info](#pg-stat-statements-info) | 1 |
| [raster_columns](#raster-columns) | 0 |
| [raster_overviews](#raster-overviews) | 0 |
| [spatial_ref_sys](#spatial-ref-sys) | 8,500 |
| [station](#station) | 551 |
| [stats](#stats) | 403 |
| [task_profile](#task-profile) | 568,157 |

## Enabled PostgreSQL Plugins

| Plugin Name | Version |
|-------------|--------|
| hstore | 1\.6 |
| pg\_stat\_statements | 1\.9 |
| plpgsql | 1\.0 |
| postgis | 3\.4\.2 |
| postgis\_raster | 3\.4\.2 |
| postgis\_topology | 3\.4\.2 |
| timescaledb | 2\.16\.1 |

## Table: aemo_facility_data

Total rows: 0

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| aemo_source | USER-DEFINED | N/A | No |
| source_date | date | N/A | No |
| name | text | N/A | Yes |
| name_network | text | N/A | Yes |
| network_region | text | N/A | Yes |
| fueltech_id | text | N/A | Yes |
| status_id | text | N/A | Yes |
| duid | text | N/A | Yes |
| units_no | integer | N/A | Yes |
| capacity_registered | numeric | N/A | Yes |
| closure_year_expected | integer | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE aemo_facility_data
(
    aemo_source aemodatasource NOT NULL,
    source_date date NOT NULL,
    name text NULL,
    name_network text NULL,
    network_region text NULL,
    fueltech_id text NULL,
    status_id text NULL,
    duid text NULL,
    units_no integer NULL,
    capacity_registered numeric NULL,
    closure_year_expected integer NULL
);

```

### Constraints

- PRIMARY KEY (aemo_source, source_date)

### Indexes

- CREATE UNIQUE INDEX aemo_facility_data_pkey ON public.aemo_facility_data USING btree (aemo_source, source_date)

## Table: aemo_market_notices

Total rows: 815

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| notice_id | integer | N/A | No |
| notice_type | character varying | N/A | No |
| creation_date | timestamp without time zone | N/A | No |
| issue_date | timestamp without time zone | N/A | No |
| external_reference | text | N/A | Yes |
| reason | text | N/A | No |

### Create Table Statement

```sql
CREATE TABLE aemo_market_notices
(
    notice_id integer NOT NULL,
    notice_type character varying NOT NULL,
    creation_date timestamp without time zone NOT NULL,
    issue_date timestamp without time zone NOT NULL,
    external_reference text NULL,
    reason text NOT NULL
);

```

### Constraints

- PRIMARY KEY (notice_id)

### Indexes

- CREATE UNIQUE INDEX aemo_market_notices_pkey ON public.aemo_market_notices USING btree (notice_id)
- CREATE INDEX ix_aemo_market_notices_creation_date ON public.aemo_market_notices USING btree (creation_date)
- CREATE INDEX ix_aemo_market_notices_notice_id ON public.aemo_market_notices USING btree (notice_id)
- CREATE INDEX ix_aemo_market_notices_notice_type ON public.aemo_market_notices USING btree (notice_type)

### Sample Data

| notice\_id | notice\_type | creation\_date | issue\_date | external\_reference | reason |
| --- | --- | --- | --- | --- | --- |
| 118095 | MARKET INTERVENTION | 2024\-09\-03 13:59:35 | 2024\-09\-03 00:00:00 | Direction \- SA region 03/09/2024 | AEMO ELECTRICITY MARKET NOTICE

Direction \- SA region 03/09/2024

In accordance with section 116 of the National Electricity Law, AEMO has issued a direction to a participant in the SA region\. For the\.\.\. |
| 118178 | RECLASSIFY CONTINGENCY | 2024\-09\-08 08:14:09 | 2024\-09\-08 08:14:00 | Cancellation of a Non\-Credible Contingency Event: Farrell\-John Butters line and Farrell\-Rosebery\-Newton\-Queenstown line in TAS1 due to Lightning\. | AEMO ELECTRICITY MARKET NOTICE

Cancellation of reclassification of a Non\-Credible Contingency Event as a Credible Contingency Event due to Lightning\. AEMO considers the simultaneous trip of the follo\.\.\. |
| 117364 | MARKET INTERVENTION | 2024\-07\-19 11:34:15 | 2024\-07\-19 00:00:00 | Update \- Foreseeable AEMO intervention in SA region | AEMO ELECTRICITY MARKET NOTICE

Update \- Foreseeable AEMO intervention in SA region

Refer AEMO Electricity Market Notice 117362

AEMO has identified a foreseeable circumstance that may require an AEM\.\.\. |
| 117616 | PRICES SUBJECT TO REVIEW | 2024\-08\-09 19:50:19 | 2024\-08\-09 00:00:00 | \[EventId:202408091955\_review\] Prices for interval 09\-Aug\-2024 19:55 are subject to review | AEMO ELECTRICITY MARKET NOTICE

Issued by Australian Energy Market Operator Ltd at 1950 hrs on 9 August 2024

PRICES ARE SUBJECT TO REVIEW for trading interval 09\-Aug\-2024 19:55\.

AEMO is reviewing th\.\.\. |
| 117476 | RECLASSIFY CONTINGENCY | 2024\-07\-26 16:36:25 | 2024\-07\-26 00:00:00 | Reclassification of a Non\-Credible Contingency Event: Armidale \- Dumaresq 8C 330kV line and Armidale \- Sapphire WF 8E 330kV line in NSW1 due to Lightning\. | AEMO ELECTRICITY MARKET NOTICE

Reclassification of a Non\-Credible Contingency Event as a Credible Contingency Event due to Lightning\. AEMO considers the simultaneous trip of the following circuits to\.\.\. |

## Table: alembic_version

Total rows: 1

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| version_num | character varying | 32 | No |

### Create Table Statement

```sql
CREATE TABLE alembic_version
(
    version_num character varying(32) NOT NULL
);

```

### Constraints

- PRIMARY KEY (version_num)

### Indexes

- CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num)

### Sample Data

| version\_num |
| --- |
| 6f0b9e05ba9f |

## Table: api_keys

Total rows: 1

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| keyid | text | N/A | No |
| description | text | N/A | Yes |
| revoked | boolean | N/A | No |
| created_at | timestamp with time zone | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE api_keys
(
    keyid text NOT NULL,
    description text NULL,
    revoked boolean NOT NULL,
    created_at timestamp with time zone NULL
);

```

### Constraints

- PRIMARY KEY (keyid)

### Indexes

- CREATE UNIQUE INDEX api_keys_pkey ON public.api_keys USING btree (keyid)

### Sample Data

| keyid | description | revoked | created\_at |
| --- | --- | --- | --- |
| DQwfwdHCzjBmnM5yMgkAVg | opennem default | False | 2021\-05\-27 12:28:38\.314071\+00:00 |

## Table: at_facility_daily

Total rows: 2,885,368

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| trading_day | timestamp with time zone | N/A | No |
| network_id | text | N/A | No |
| facility_code | text | N/A | No |
| fueltech_id | text | N/A | Yes |
| energy | numeric | N/A | Yes |
| market_value | numeric | N/A | Yes |
| emissions | numeric | N/A | Yes |
| network_region | text | N/A | No |

### Create Table Statement

```sql
CREATE TABLE at_facility_daily
(
    trading_day timestamp with time zone NOT NULL,
    network_id text NOT NULL,
    facility_code text NOT NULL,
    fueltech_id text NULL,
    energy numeric NULL,
    market_value numeric NULL,
    emissions numeric NULL,
    network_region text NOT NULL
);

```

### Constraints

- PRIMARY KEY (trading_day, network_id, facility_code)

### Indexes

- CREATE UNIQUE INDEX at_facility_daily_pkey ON public.at_facility_daily USING btree (trading_day, network_id, facility_code)
- CREATE UNIQUE INDEX idx_at_facility_daily_facility_code_network_id_trading_day ON public.at_facility_daily USING btree (network_id, facility_code, trading_day)
- CREATE INDEX idx_at_facility_daily_network_id_trading_interval ON public.at_facility_daily USING btree (network_id, trading_day DESC)
- CREATE INDEX idx_at_facility_daily_trading_interval_facility_code ON public.at_facility_daily USING btree (trading_day, facility_code)
- CREATE INDEX idx_at_facility_day_facility_code_trading_interval ON public.at_facility_daily USING btree (facility_code, trading_day DESC)
- CREATE INDEX ix_at_facility_daily_facility_code ON public.at_facility_daily USING btree (facility_code)
- CREATE INDEX ix_at_facility_daily_trading_day ON public.at_facility_daily USING btree (trading_day)

### Sample Data

| trading\_day | network\_id | facility\_code | fueltech\_id | energy | market\_value | emissions | network\_region |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2024\-05\-11 00:00:00\+00:00 | NEM | BBTHREE1 | gas\_ocgt | 986\.7041666666666649 | 137765\.09400416666679535274999999999995 | 655\.846610455249998825724686 | TAS1 |
| 2016\-06\-29 00:00:00\+00:00 | NEM | VP6 | coal\_black | 13148\.11104875000020 | 1328385\.9765881148973375392 | 11942\.4961894648633191610180 | NSW1 |
| 2018\-02\-19 00:00:00\+00:00 | NEM | SNOWSTH1 | wind | 2104\.749997499999975 | 142947\.11865076421893828454 | 0E\-16 | SA1 |
| 2009\-03\-08 00:00:00\+00:00 | NEM | NEM\_FLOW\_VIC1\_IMPORTS | imports | 0 | 0 | 0 | VIC1 |
| 2002\-07\-13 00:00:00\+00:00 | NEM | MM4 | coal\_black | 0 | 0 | 0 | NSW1 |

## Table: at_network_demand

Total rows: 62,753

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| trading_day | timestamp with time zone | N/A | No |
| network_id | text | N/A | No |
| network_region | text | N/A | No |
| demand_energy | numeric | N/A | Yes |
| demand_market_value | numeric | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE at_network_demand
(
    trading_day timestamp with time zone NOT NULL,
    network_id text NOT NULL,
    network_region text NOT NULL,
    demand_energy numeric NULL,
    demand_market_value numeric NULL
);

```

### Constraints

- PRIMARY KEY (trading_day, network_id, network_region)
- FOREIGN KEY (network_id) REFERENCES network(code)

### Indexes

- CREATE UNIQUE INDEX at_network_demand_pkey ON public.at_network_demand USING btree (trading_day, network_id, network_region)
- CREATE INDEX idx_at_network_demand_network_id_trading_interval ON public.at_network_demand USING btree (network_id, trading_day DESC)
- CREATE INDEX idx_at_network_demand_trading_interval_network_region ON public.at_network_demand USING btree (trading_day, network_id, network_region)
- CREATE INDEX ix_at_network_demand_network_id ON public.at_network_demand USING btree (network_id)
- CREATE INDEX ix_at_network_demand_trading_day ON public.at_network_demand USING btree (trading_day)

### Sample Data

| trading\_day | network\_id | network\_region | demand\_energy | demand\_market\_value |
| --- | --- | --- | --- | --- |
| 2008\-10\-12 00:00:00\+00:00 | NEM | SA1 | 33\.31500036416666666663 | 148348\.2991247666666675794000 |
| 2006\-06\-02 00:00:00\+00:00 | NEM | VIC1 | 156\.03657202500000000005 | 594674\.4992788333333335833000 |
| 2018\-08\-17 00:00:00\+00:00 | NEM | SA1 | 35\.84175699166666666675 | 2563772\.7732292804250070889134000 |
| 2001\-02\-12 00:00:00\+00:00 | NEM | QLD1 | 19\.66234833333333333330 | 355190\.5846083333333326484000 |
| 2017\-11\-03 00:00:00\+00:00 | WEM | WEM | None | None |

## Table: at_network_flows

Total rows: 7,917,760

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| trading_interval | timestamp with time zone | N/A | No |
| network_id | text | N/A | No |
| network_region | text | N/A | No |
| energy_imports | numeric | N/A | Yes |
| energy_exports | numeric | N/A | Yes |
| emissions_imports | numeric | N/A | Yes |
| emissions_exports | numeric | N/A | Yes |
| market_value_imports | numeric | N/A | Yes |
| market_value_exports | numeric | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE at_network_flows
(
    trading_interval timestamp with time zone NOT NULL,
    network_id text NOT NULL,
    network_region text NOT NULL,
    energy_imports numeric NULL,
    energy_exports numeric NULL,
    emissions_imports numeric NULL,
    emissions_exports numeric NULL,
    market_value_imports numeric NULL,
    market_value_exports numeric NULL
);

```

### Constraints

- PRIMARY KEY (trading_interval, network_id, network_region)
- FOREIGN KEY (network_id) REFERENCES network(code)

### Indexes

- CREATE UNIQUE INDEX at_network_flows_pkey ON public.at_network_flows USING btree (trading_interval, network_id, network_region)
- CREATE INDEX idx_at_network_flows_trading_interval_facility_code ON public.at_network_flows USING btree (trading_interval, network_id, network_region)
- CREATE INDEX idx_at_network_flowsy_network_id_trading_interval ON public.at_network_flows USING btree (network_id, trading_interval DESC)
- CREATE INDEX ix_at_network_flows_network_id ON public.at_network_flows USING btree (network_id)
- CREATE INDEX ix_at_network_flows_network_region ON public.at_network_flows USING btree (network_region)
- CREATE INDEX ix_at_network_flows_trading_interval ON public.at_network_flows USING btree (trading_interval)

### Sample Data

| trading\_interval | network\_id | network\_region | energy\_imports | energy\_exports | emissions\_imports | emissions\_exports | market\_value\_imports | market\_value\_exports |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2012\-11\-17 16:30:00\+00:00 | NEM | QLD1 | 0\.0 | 64\.11953166666666 | 0\.0 | 56\.84079945146653 | 0\.0 | 0\.0 |
| 2019\-05\-30 11:45:00\+00:00 | NEM | TAS1 | 0\.0 | 7\.833333333333333 | 0\.0 | 0\.0 | 0\.0 | 0\.0 |
| 2016\-12\-28 18:40:00\+00:00 | NEM | QLD1 | 0\.0 | 31\.643896666666667 | 0\.0 | 26\.316435265360596 | 0\.0 | 0\.0 |
| 2020\-02\-14 00:50:00\+00:00 | NEM | SA1 | 0\.9776225 | 0\.0 | 0\.8725611335293364 | 0\.0 | 0\.0 | 0\.0 |
| 2015\-11\-20 12:25:00\+00:00 | NEM | SA1 | 8\.463306666666666 | 0\.0 | 9\.516493528278268 | 0\.0 | 0\.0 | 0\.0 |

## Table: at_network_flows_v3

Total rows: 0

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| trading_interval | timestamp with time zone | N/A | No |
| network_id | text | N/A | No |
| network_region | text | N/A | No |
| energy_imports | numeric | N/A | Yes |
| energy_exports | numeric | N/A | Yes |
| market_value_imports | numeric | N/A | Yes |
| market_value_exports | numeric | N/A | Yes |
| emissions_imports | numeric | N/A | Yes |
| emissions_exports | numeric | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE at_network_flows_v3
(
    trading_interval timestamp with time zone NOT NULL,
    network_id text NOT NULL,
    network_region text NOT NULL,
    energy_imports numeric NULL,
    energy_exports numeric NULL,
    market_value_imports numeric NULL,
    market_value_exports numeric NULL,
    emissions_imports numeric NULL,
    emissions_exports numeric NULL
);

```

### Constraints

- PRIMARY KEY (trading_interval, network_id, network_region)
- FOREIGN KEY (network_id) REFERENCES network(code)

### Indexes

- CREATE UNIQUE INDEX at_network_flows_v3_pkey ON public.at_network_flows_v3 USING btree (trading_interval, network_id, network_region)
- CREATE INDEX idx_at_network_flows_v3_trading_interval_facility_code ON public.at_network_flows_v3 USING btree (trading_interval, network_id, network_region)
- CREATE INDEX idx_at_network_flowsy_v3_network_id_trading_interval ON public.at_network_flows_v3 USING btree (network_id, trading_interval DESC)
- CREATE INDEX ix_at_network_flows_v3_network_id ON public.at_network_flows_v3 USING btree (network_id)
- CREATE INDEX ix_at_network_flows_v3_network_region ON public.at_network_flows_v3 USING btree (network_region)
- CREATE INDEX ix_at_network_flows_v3_trading_interval ON public.at_network_flows_v3 USING btree (trading_interval)

## Table: balancing_summary

Total rows: 11,323,665

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| interval | timestamp without time zone | N/A | No |
| network_id | text | N/A | No |
| network_region | text | N/A | No |
| forecast_load | numeric | N/A | Yes |
| generation_scheduled | numeric | N/A | Yes |
| generation_non_scheduled | numeric | N/A | Yes |
| generation_total | numeric | N/A | Yes |
| price | numeric | N/A | Yes |
| is_forecast | boolean | N/A | Yes |
| net_interchange | numeric | N/A | Yes |
| demand_total | numeric | N/A | Yes |
| price_dispatch | numeric | N/A | Yes |
| net_interchange_trading | numeric | N/A | Yes |
| demand | numeric | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE balancing_summary
(
    interval timestamp without time zone NOT NULL,
    network_id text NOT NULL,
    network_region text NOT NULL,
    forecast_load numeric NULL,
    generation_scheduled numeric NULL,
    generation_non_scheduled numeric NULL,
    generation_total numeric NULL,
    price numeric NULL,
    is_forecast boolean NULL,
    net_interchange numeric NULL,
    demand_total numeric NULL,
    price_dispatch numeric NULL,
    net_interchange_trading numeric NULL,
    demand numeric NULL
);

```

### Constraints

- PRIMARY KEY ("interval", network_id, network_region)

### Indexes

- CREATE UNIQUE INDEX pk_balancing_summary_pkey ON public.balancing_summary USING btree ("interval", network_id, network_region)
- CREATE INDEX balancing_summary_new_interval_idx ON public.balancing_summary USING btree ("interval" DESC)
- CREATE INDEX idx_balancing_summary_interval_network_region ON public.balancing_summary USING btree ("interval" DESC, network_id, network_region)
- CREATE INDEX idx_balancing_summary_network_id_interval ON public.balancing_summary USING btree (network_id, "interval" DESC)
- CREATE INDEX ix_balancing_summary_interval ON public.balancing_summary USING btree ("interval")

### Sample Data

| interval | network\_id | network\_region | forecast\_load | generation\_scheduled | generation\_non\_scheduled | generation\_total | price | is\_forecast | net\_interchange | demand\_total | price\_dispatch | net\_interchange\_trading | demand |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2006\-12\-06 18:50:00 | NEM | TAS1 | None | None | None | None | None | False | \-424\.2 | 1265\.8457 | None | None | 1186\.26 |
| 2020\-10\-17 01:45:00 | NEM | SA1 | None | None | None | None | None | False | \-277\.32 | 1190\.803550 | 54\.44 | None | 1146\.33 |
| 2016\-01\-29 06:15:00 | NEM | TAS1 | None | None | None | None | None | False | 0 | 1158\.67235 | 115\.3 | None | 1136\.53 |
| 2010\-04\-05 14:10:00 | NEM | SA1 | None | None | None | None | None | False | \-276\.86 | 1567\.9741 | 24\.63635 | None | 1532\.95 |
| 2011\-04\-24 08:15:00 | NEM | VIC1 | None | None | None | None | None | False | 1248 | 4725\.1985 | 21\.8871 | None | 4678\.32 |

## Table: bom_observation

Total rows: 5,920,234

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| observation_time | timestamp with time zone | N/A | No |
| station_id | text | N/A | No |
| temp_apparent | numeric | N/A | Yes |
| temp_air | numeric | N/A | Yes |
| press_qnh | numeric | N/A | Yes |
| wind_dir | text | N/A | Yes |
| wind_spd | numeric | N/A | Yes |
| cloud | text | N/A | Yes |
| cloud_type | text | N/A | Yes |
| humidity | numeric | N/A | Yes |
| wind_gust | numeric | N/A | Yes |
| temp_max | numeric | N/A | Yes |
| temp_min | numeric | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE bom_observation
(
    observation_time timestamp with time zone NOT NULL,
    station_id text NOT NULL,
    temp_apparent numeric NULL,
    temp_air numeric NULL,
    press_qnh numeric NULL,
    wind_dir text NULL,
    wind_spd numeric NULL,
    cloud text NULL,
    cloud_type text NULL,
    humidity numeric NULL,
    wind_gust numeric NULL,
    temp_max numeric NULL,
    temp_min numeric NULL
);

```

### Constraints

- PRIMARY KEY (observation_time, station_id)
- FOREIGN KEY (station_id) REFERENCES bom_station(code)

### Indexes

- CREATE UNIQUE INDEX bom_observation_pkey ON public.bom_observation USING btree (observation_time, station_id)
- CREATE INDEX ix_bom_observation_observation_time ON public.bom_observation USING btree (observation_time)

### Sample Data

| observation\_time | station\_id | temp\_apparent | temp\_air | press\_qnh | wind\_dir | wind\_spd | cloud | cloud\_type | humidity | wind\_gust | temp\_max | temp\_min |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020\-12\-10 15:10:00\+00:00 | 250104 | 3\.4 | 5\.2 | None | ESE | 4 |  |  | 100 | 6 | None | None |
| 2021\-04\-16 04:00:00\+00:00 | 023878 | 12\.8 | 14\.4 | 1024\.5 | SSW | 6 |  |  | 65 | 9 | None | None |
| 2002\-08\-01 09:00:00\+00:00 | 040913 | 13\.3 | 16\.5 | None | None | None | None | None | 12\.6 | None | None | None |
| 2015\-08\-06 10:30:00\+00:00 | 040913 | 10\.3 | 16\.2 | None | None | None | None | None | 7\.7 | None | None | None |
| 2021\-02\-14 00:00:00\+00:00 | 092114 | 21\.1 | 21\.7 | 1018\.3 | ENE | 9 |  |  | 60 | 17 | None | None |

## Table: bom_station

Total rows: 773

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| code | text | N/A | No |
| state | text | N/A | Yes |
| name | text | N/A | Yes |
| registered | date | N/A | Yes |
| geom | USER-DEFINED | N/A | Yes |
| feed_url | text | N/A | Yes |
| is_capital | boolean | N/A | Yes |
| name_alias | text | N/A | Yes |
| priority | integer | N/A | Yes |
| website_url | text | N/A | Yes |
| altitude | integer | N/A | Yes |
| web_code | text | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE bom_station
(
    code text NOT NULL,
    state text NULL,
    name text NULL,
    registered date NULL,
    geom geometry(Point,4326) NULL,
    feed_url text NULL,
    is_capital boolean NULL,
    name_alias text NULL,
    priority integer NULL,
    website_url text NULL,
    altitude integer NULL,
    web_code text NULL
);

```

### Constraints

- PRIMARY KEY (code)

### Indexes

- CREATE UNIQUE INDEX bom_station_pkey ON public.bom_station USING btree (code)
- CREATE INDEX idx_bom_station_geom ON public.bom_station USING gist (geom)
- CREATE INDEX idx_bom_station_priority ON public.bom_station USING btree (priority)

### Sample Data

| code | state | name | registered | geom | feed\_url | is\_capital | name\_alias | priority | website\_url | altitude | web\_code |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 069134 | NSW | BATEMANS BAY \(CATALINA COUNTRY CLUB\) | None | 0101000020E6100000AE47E17A14C662405C8FC2F528DC41C0 | http://www\.bom\.gov\.au/fwo/IDN60801/IDN60801\.94941\.json | False | Batemans Bay | 5 | http://www\.bom\.gov\.au/products/IDN60801/IDN60801\.94941\.shtml | 11 | None |
| 059151 | NSW | COFFS HARBOUR AIRPORT | None | 0101000020E6100000A4703D0AD723634052B81E85EB513EC0 | http://www\.bom\.gov\.au/fwo/IDN60801/IDN60801\.95729\.json | False | Coffs Harbour Airport | 5 | http://www\.bom\.gov\.au/products/IDN60801/IDN60801\.95729\.shtml | 3 | None |
| 003003 | WA | BROOME AIRPORT | None | 0101000020E61000008FC2F5285C8F5E403333333333F331C0 | http://www\.bom\.gov\.au/fwo/IDW60801/IDW60801\.94203\.json | False | Broome | 5 | http://www\.bom\.gov\.au/products/IDW60801/IDW60801\.94203\.shtml | 7 | None |
| 250104 | NSW | ACT PCS1 | None | 0101000020E6100000CDCCCCCCCC9C624014AE47E17AB441C0 | http://www\.bom\.gov\.au/fwo/IDN60801/IDN60801\.99145\.json | False | ACT PCS1 | 5 | http://www\.bom\.gov\.au/products/IDN60801/IDN60801\.99145\.shtml | 1338 | None |
| 058198 | NSW | BALLINA AIRPORT AWS | None | 0101000020E610000052B81E85EB316340D7A3703D0AD73CC0 | http://www\.bom\.gov\.au/fwo/IDN60801/IDN60801\.94596\.json | False | Ballina | 5 | http://www\.bom\.gov\.au/products/IDN60801/IDN60801\.94596\.shtml | 1 | None |

## Table: crawl_history

Total rows: 788,306

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| source | USER-DEFINED | N/A | No |
| crawler_name | text | N/A | No |
| network_id | text | N/A | No |
| interval | timestamp with time zone | N/A | No |
| inserted_records | integer | N/A | Yes |
| crawled_time | timestamp with time zone | N/A | Yes |
| processed_time | timestamp with time zone | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE crawl_history
(
    source crawlersource NOT NULL,
    crawler_name text NOT NULL,
    network_id text NOT NULL,
    interval timestamp with time zone NOT NULL,
    inserted_records integer NULL,
    crawled_time timestamp with time zone NULL,
    processed_time timestamp with time zone NULL
);

```

### Constraints

- PRIMARY KEY (source, crawler_name, network_id, "interval")
- FOREIGN KEY (network_id) REFERENCES network(code)

### Indexes

- CREATE UNIQUE INDEX crawl_history_pkey ON public.crawl_history USING btree (source, crawler_name, network_id, "interval")
- CREATE INDEX ix_crawl_history_interval ON public.crawl_history USING btree ("interval")

### Sample Data

| source | crawler\_name | network\_id | interval | inserted\_records | crawled\_time | processed\_time |
| --- | --- | --- | --- | --- | --- | --- |
| nemweb | au\.nemweb\.dispatch\_is | NEM | 2023\-02\-12 20:30:00\+00:00 | 16 | None | 2023\-02\-12 10:30:18\+00:00 |
| nemweb | au\.nemweb\.dispatch\_scada | NEM | 2022\-09\-29 16:45:00\+00:00 | 415 | None | 2022\-09\-29 06:45:55\+00:00 |
| nemweb | au\.nemweb\.dispatch\_is | NEM | 2023\-03\-15 18:05:00\+00:00 | 16 | None | 2023\-03\-15 08:05:52\+00:00 |
| nemweb | au\.nemweb\.current\.dispatch\_scada | NEM | 2024\-01\-13 18:05:00\+00:00 | 455 | None | 2024\-01\-15 00:45:03\+00:00 |
| nemweb | au\.nemweb\.current\.trading\_is | NEM | 2024\-05\-17 03:20:00\+00:00 | 5 | None | 2024\-05\-16 17:20:04\+00:00 |

## Table: crawl_meta

Total rows: 50

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| spider_name | text | N/A | No |
| data | jsonb | N/A | Yes |
| created_at | timestamp with time zone | N/A | Yes |
| updated_at | timestamp with time zone | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE crawl_meta
(
    spider_name text NOT NULL,
    data jsonb NULL,
    created_at timestamp with time zone NULL,
    updated_at timestamp with time zone NULL
);

```

### Constraints

- PRIMARY KEY (spider_name)

### Indexes

- CREATE UNIQUE INDEX crawl_meta_pkey ON public.crawl_meta USING btree (spider_name)
- CREATE INDEX ix_crawl_meta_data ON public.crawl_meta USING btree (data)

### Sample Data

| spider\_name | data | created\_at | updated\_at |
| --- | --- | --- | --- |
| au\.nem\.rooftop | \{'version': '2', 'last\_crawled': '2022\-08\-09T12:10:40\+10:00', 'server\_latest': '2022\-06\-27T11:00:00\+10:00', 'latest\_processed': '2022\-06\-27T11:00:00\+10:00'\} | 2022\-06\-10 05:45:55\.969542\+00:00 | 2022\-08\-09 02:10:40\.472064\+00:00 |
| au\.bom\.capitals | \{'version': '2', 'last\_crawled': '2024\-08\-29T01:40:17\+10:00', 'server\_latest': '2024\-08\-29T00:00:00\+10:00', 'latest\_processed': '2024\-08\-29T00:00:00\+10:00'\} | 2022\-06\-10 05:54:17\.716553\+00:00 | 2024\-08\-28 15:40:18\.004589\+00:00 |
| au\.wemde\.history\.trading\_report | \{'last\_crawled': '2024\-08\-03T10:53:32\+10:00', 'server\_latest': '2024\-08\-01T00:00:00', 'latest\_interval': '2024\-08\-02T07:30:00\+08:00', 'latest\_processed': '2024\-01\-15T11:46:14\+11:00'\} | 2024\-01\-14 20:48:04\.717802\+00:00 | 2024\-08\-03 00:53:32\.173025\+00:00 |
| au\.nemweb\.archive\.dispatch | \{'version': '2', 'last\_crawled': '2024\-09\-04T00:33:39\+10:00'\} | 2022\-07\-21 07:45:25\.695029\+00:00 | 2024\-09\-03 14:33:39\.935215\+00:00 |
| au\.nemweb\.current\.trading\_is | \{'version': '2', 'last\_crawled': '2024\-09\-10T09:30:30\+10:00', 'server\_latest': '2024\-08\-03T10:50:00\+10:00', 'latest\_processed': '2024\-08\-03T10:50:00\+10:00'\} | 2023\-09\-04 10:13:47\.028003\+00:00 | 2024\-09\-09 23:30:30\.326070\+00:00 |

## Table: facility

Total rows: 787

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| created_by | text | N/A | Yes |
| created_at | timestamp with time zone | N/A | Yes |
| updated_at | timestamp with time zone | N/A | Yes |
| id | integer | N/A | No |
| network_id | text | N/A | No |
| fueltech_id | text | N/A | Yes |
| status_id | text | N/A | Yes |
| station_id | integer | N/A | Yes |
| code | text | N/A | No |
| network_code | text | N/A | Yes |
| network_region | text | N/A | Yes |
| network_name | text | N/A | Yes |
| active | boolean | N/A | Yes |
| dispatch_type | USER-DEFINED | N/A | No |
| capacity_registered | numeric | N/A | Yes |
| registered | timestamp without time zone | N/A | Yes |
| deregistered | timestamp without time zone | N/A | Yes |
| unit_id | integer | N/A | Yes |
| unit_number | integer | N/A | Yes |
| unit_alias | text | N/A | Yes |
| unit_capacity | numeric | N/A | Yes |
| approved | boolean | N/A | Yes |
| approved_by | text | N/A | Yes |
| approved_at | timestamp with time zone | N/A | Yes |
| emissions_factor_co2 | numeric | N/A | Yes |
| interconnector | boolean | N/A | Yes |
| interconnector_region_to | text | N/A | Yes |
| data_first_seen | timestamp with time zone | N/A | Yes |
| data_last_seen | timestamp with time zone | N/A | Yes |
| expected_closure_date | timestamp without time zone | N/A | Yes |
| expected_closure_year | integer | N/A | Yes |
| interconnector_region_from | text | N/A | Yes |
| emission_factor_source | text | N/A | Yes |
| include_in_geojson | boolean | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE facility
(
    created_by text NULL,
    created_at timestamp with time zone NULL,
    updated_at timestamp with time zone NULL,
    id integer NOT NULL,
    network_id text NOT NULL,
    fueltech_id text NULL,
    status_id text NULL,
    station_id integer NULL,
    code text NOT NULL,
    network_code text NULL,
    network_region text NULL,
    network_name text NULL,
    active boolean NULL,
    dispatch_type dispatchtype NOT NULL,
    capacity_registered numeric NULL,
    registered timestamp without time zone NULL,
    deregistered timestamp without time zone NULL,
    unit_id integer NULL,
    unit_number integer NULL,
    unit_alias text NULL,
    unit_capacity numeric NULL,
    approved boolean NULL,
    approved_by text NULL,
    approved_at timestamp with time zone NULL,
    emissions_factor_co2 numeric NULL,
    interconnector boolean NULL,
    interconnector_region_to text NULL,
    data_first_seen timestamp with time zone NULL,
    data_last_seen timestamp with time zone NULL,
    expected_closure_date timestamp without time zone NULL,
    expected_closure_year integer NULL,
    interconnector_region_from text NULL,
    emission_factor_source text NULL,
    include_in_geojson boolean NULL
);

```

### Constraints

- UNIQUE (network_id, code)
- PRIMARY KEY (id)
- FOREIGN KEY (fueltech_id) REFERENCES fueltech(code)
- FOREIGN KEY (station_id) REFERENCES station(id)
- FOREIGN KEY (status_id) REFERENCES facility_status(code)
- FOREIGN KEY (network_id) REFERENCES network(code)

### Indexes

- CREATE UNIQUE INDEX excl_facility_network_id_code ON public.facility USING btree (network_id, code)
- CREATE UNIQUE INDEX facility_pkey ON public.facility USING btree (id)
- CREATE INDEX idx_facility_fueltech_id ON public.facility USING btree (fueltech_id)
- CREATE INDEX idx_facility_station_id ON public.facility USING btree (station_id)
- CREATE UNIQUE INDEX ix_facility_code ON public.facility USING btree (code)
- CREATE INDEX ix_facility_data_first_seen ON public.facility USING btree (data_first_seen)
- CREATE INDEX ix_facility_data_last_seen ON public.facility USING btree (data_last_seen)
- CREATE INDEX ix_facility_interconnector ON public.facility USING btree (interconnector)
- CREATE INDEX ix_facility_interconnector_region_from ON public.facility USING btree (interconnector_region_from)
- CREATE INDEX ix_facility_interconnector_region_to ON public.facility USING btree (interconnector_region_to)
- CREATE INDEX ix_facility_network_code ON public.facility USING btree (network_code)
- CREATE INDEX ix_facility_network_region ON public.facility USING btree (network_region)

### Sample Data

| created\_by | created\_at | updated\_at | id | network\_id | fueltech\_id | status\_id | station\_id | code | network\_code | network\_region | network\_name | active | dispatch\_type | capacity\_registered | registered | deregistered | unit\_id | unit\_number | unit\_alias | unit\_capacity | approved | approved\_by | approved\_at | emissions\_factor\_co2 | interconnector | interconnector\_region\_to | data\_first\_seen | data\_last\_seen | expected\_closure\_date | expected\_closure\_year | interconnector\_region\_from | emission\_factor\_source | include\_in\_geojson |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| opennem\.registry | 2020\-12\-09 15:33:15\.759865\+00:00 | 2023\-03\-31 04:51:10\.037362\+00:00 | 48 | NEM | solar\_utility | operating | 37 | BARCSF1 | NEM | QLD1 | None | True | GENERATOR | 10\.0 | None | None | None | None | None | None | True | None | 2020\-12\-09 15:33:15\.759844\+00:00 | 0\.0 | False | None | 2016\-12\-21 04:55:00\+00:00 | 2024\-08\-03 00:50:00\+00:00 | None | None | None | None | True |
| opennem\.registry | 2020\-12\-09 15:33:45\.631035\+00:00 | 2023\-03\-31 04:51:23\.532531\+00:00 | 211 | NEM | battery\_charging | operating | 153 | HPRL1 | NEM | SA1 | None | True | GENERATOR | 150\.0 | None | None | None | None | None | None | True | None | 2020\-12\-09 15:33:45\.631022\+00:00 | 0\.0 | False | None | 2017\-11\-24 00:05:00\+00:00 | 2024\-08\-03 00:50:00\+00:00 | None | None | None | None | True |
| opennem\.init | 2022\-07\-12 00:23:39\.933460\+00:00 | 2023\-12\-06 05:04:48\.337659\+00:00 | 742 | NEM | battery\_discharging | operating | 524 | QBYNBG1 | None | NSW1 | None | True | GENERATOR | 100\.0 | None | None | None | None | None | None | True | None | None | 0\.0 | False | None | 2022\-07\-06 23:05:00\+00:00 | 2024\-08\-02 19:55:00\+00:00 | None | None | None | None | True |
| opennem\.registry | 2020\-12\-09 15:34:34\.341322\+00:00 | 2024\-06\-07 13:11:32\.502093\+00:00 | 441 | NEM | gas\_ocgt | operating | 317 | URANQ11 | NEM | NSW1 | None | True | GENERATOR | 166\.0 | None | None | None | None | None | None | True | None | 2020\-12\-09 15:34:34\.341307\+00:00 | 0\.72427163 | False | None | 2008\-10\-27 08:50:00\+00:00 | 2024\-08\-02 13:15:00\+00:00 | None | None | None | None | True |
| opennem\.importer\.trading\_flows | 2021\-03\-06 09:41:38\.312087\+00:00 | 2021\-03\-06 20:41:38\.477766\+00:00 | 624 | NEM | exports | operating | 448 | NEM\_FLOW\_VIC1\_EXPORTS | None | VIC1 | None | True | GENERATOR | None | None | None | None | None | None | None | True | opennem\.importer\.trading\_flows | None | None | False | None | 2009\-06\-30 14:25:00\+00:00 | 2021\-04\-30 13:55:00\+00:00 | None | None | None | None | True |

## Table: facility_scada

Total rows: 769,217,358

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| network_id | text | N/A | No |
| interval | timestamp without time zone | N/A | No |
| facility_code | text | N/A | No |
| generated | numeric | N/A | Yes |
| eoi_quantity | numeric | N/A | Yes |
| is_forecast | boolean | N/A | No |
| energy_quality_flag | numeric | N/A | No |
| energy | numeric | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE facility_scada
(
    network_id text NOT NULL,
    interval timestamp without time zone NOT NULL,
    facility_code text NOT NULL,
    generated numeric NULL,
    eoi_quantity numeric NULL,
    is_forecast boolean NOT NULL,
    energy_quality_flag numeric NOT NULL,
    energy numeric NULL
);

```

### Constraints

- PRIMARY KEY (network_id, "interval", facility_code, is_forecast)

### Indexes

- CREATE UNIQUE INDEX facility_scada_new_pkey ON public.facility_scada USING btree (network_id, "interval", facility_code, is_forecast)
- CREATE INDEX facility_scada_new_interval_idx ON public.facility_scada USING btree ("interval" DESC)
- CREATE INDEX idx_facility_scada_facility_code_interval ON public.facility_scada USING btree (facility_code, "interval" DESC)
- CREATE INDEX idx_facility_scada_interval_facility_code ON public.facility_scada USING btree ("interval", facility_code)
- CREATE INDEX idx_facility_scada_interval_network ON public.facility_scada USING btree ("interval" DESC, network_id)
- CREATE INDEX idx_facility_scada_is_forecast_interval ON public.facility_scada USING btree (is_forecast, "interval")
- CREATE INDEX idx_facility_scada_network_facility_interval ON public.facility_scada USING btree (network_id, facility_code, "interval")
- CREATE INDEX idx_facility_scada_network_id ON public.facility_scada USING btree (network_id)
- CREATE INDEX idx_facility_scada_network_interval ON public.facility_scada USING btree (network_id, "interval", is_forecast)
- CREATE INDEX ix_facility_scada_facility_code ON public.facility_scada USING btree (facility_code)
- CREATE INDEX ix_facility_scada_interval ON public.facility_scada USING btree ("interval")

### Sample Data

| network\_id | interval | facility\_code | generated | eoi\_quantity | is\_forecast | energy\_quality\_flag | energy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NEM | 2011\-12\-28 03:40:00 | WG01 | 0\.0 | None | False | 1 | 0E\-20 |
| NEM | 2024\-03\-15 12:20:00 | RT\_TAS1 | 0\.0 | 0\.0 | False | 0 | 0E\-20 |
| NEM | 2013\-06\-17 18:40:00 | REECE2 | 94\.74001 | None | False | 1 | 7\.9379170833333333 |
| NEM | 2020\-09\-03 07:45:00 | GANNBL1 | 0\.03075 | None | False | 0 | 0\.00265791666666666667 |
| NEM | 2021\-01\-24 02:05:00 | MACKNTSH | 0\.0 | None | False | 0 | 0E\-20 |

## Table: facility_status

Total rows: 12

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| code | text | N/A | No |
| label | text | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE facility_status
(
    code text NOT NULL,
    label text NULL
);

```

### Constraints

- PRIMARY KEY (code)

### Indexes

- CREATE UNIQUE INDEX facility_status_pkey ON public.facility_status USING btree (code)

### Sample Data

| code | label |
| --- | --- |
| shelved | Shelved |
| committed | Committed |
| operating | Operating |
| maturing | Maturing |
| construction | Construction |

## Table: feedback

Total rows: 94

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| id | integer | N/A | No |
| subject | text | N/A | No |
| description | text | N/A | Yes |
| email | text | N/A | Yes |
| twitter | text | N/A | Yes |
| user_ip | text | N/A | Yes |
| user_agent | text | N/A | Yes |
| created_at | timestamp with time zone | N/A | Yes |
| alert_sent | boolean | N/A | No |

### Create Table Statement

```sql
CREATE TABLE feedback
(
    id integer NOT NULL,
    subject text NOT NULL,
    description text NULL,
    email text NULL,
    twitter text NULL,
    user_ip text NULL,
    user_agent text NULL,
    created_at timestamp with time zone NULL,
    alert_sent boolean NOT NULL
);

```

### Constraints

- PRIMARY KEY (id)

### Indexes

- CREATE UNIQUE INDEX feedback_pkey ON public.feedback USING btree (id)


## Table: fueltech

Total rows: 26

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| created_by | text | N/A | Yes |
| created_at | timestamp with time zone | N/A | Yes |
| updated_at | timestamp with time zone | N/A | Yes |
| code | text | N/A | No |
| label | text | N/A | Yes |
| renewable | boolean | N/A | Yes |
| fueltech_group_id | text | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE fueltech
(
    created_by text NULL,
    created_at timestamp with time zone NULL,
    updated_at timestamp with time zone NULL,
    code text NOT NULL,
    label text NULL,
    renewable boolean NULL,
    fueltech_group_id text NULL
);

```

### Constraints

- FOREIGN KEY (fueltech_group_id) REFERENCES fueltech_group(code)
- PRIMARY KEY (code)

### Indexes

- CREATE UNIQUE INDEX fueltech_pkey ON public.fueltech USING btree (code)
- CREATE INDEX idx_fueltech_code ON public.fueltech USING btree (code)

### Sample Data

| created\_by | created\_at | updated\_at | code | label | renewable | fueltech\_group\_id |
| --- | --- | --- | --- | --- | --- | --- |
| None | 2020\-12\-09 01:46:29\.963893\+00:00 | 2022\-10\-04 06:24:39\.414199\+00:00 | wind | Wind | True | wind |
| None | 2020\-12\-09 01:46:29\.376830\+00:00 | 2022\-10\-04 06:24:38\.865319\+00:00 | gas\_ccgt | Gas \(CCGT\) | False | gas |
| None | 2020\-12\-09 01:46:28\.964818\+00:00 | 2022\-10\-04 06:24:38\.513422\+00:00 | battery\_charging | Battery \(Charging\) | True | battery\_charging |
| None | 2020\-12\-09 01:46:29\.788923\+00:00 | 2022\-10\-04 06:24:39\.228913\+00:00 | solar\_utility | Solar \(Utility\) | True | solar |
| None | 2020\-12\-09 01:46:30\.195850\+00:00 | None | imports | Network Import | False | None |

## Table: fueltech_group

Total rows: 10

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| created_by | text | N/A | Yes |
| created_at | timestamp with time zone | N/A | Yes |
| updated_at | timestamp with time zone | N/A | Yes |
| code | text | N/A | No |
| label | text | N/A | Yes |
| color | text | N/A | Yes |
| renewable | boolean | N/A | No |

### Create Table Statement

```sql
CREATE TABLE fueltech_group
(
    created_by text NULL,
    created_at timestamp with time zone NULL,
    updated_at timestamp with time zone NULL,
    code text NOT NULL,
    label text NULL,
    color text NULL,
    renewable boolean NOT NULL
);

```

### Constraints

- PRIMARY KEY (code)

### Indexes

- CREATE UNIQUE INDEX fueltech_group_pkey ON public.fueltech_group USING btree (code)

### Sample Data

| created\_by | created\_at | updated\_at | code | label | color | renewable |
| --- | --- | --- | --- | --- | --- | --- |
| None | 2022\-10\-04 06:24:38\.411012\+00:00 | None | bioenergy | Bioenergy | \#A3886F | False |
| None | 2022\-10\-04 06:24:38\.263261\+00:00 | 2024\-08\-13 02:51:57\.662572\+00:00 | battery\_discharging | Battery \(Discharging\) | \#00A2FA | True |
| None | 2022\-10\-04 06:24:38\.013420\+00:00 | None | coal | Coal | \#4a4a4a | False |
| None | 2022\-10\-04 06:24:38\.163568\+00:00 | 2024\-08\-13 02:51:57\.473752\+00:00 | solar | Solar | \#FED500 | True |
| None | 2022\-10\-04 06:24:38\.461796\+00:00 | 2024\-08\-13 02:51:57\.973473\+00:00 | pumps | Pumps | \#88AFD0 | True |

## Table: geography_columns

Total rows: 0

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| f_table_catalog | name | N/A | Yes |
| f_table_schema | name | N/A | Yes |
| f_table_name | name | N/A | Yes |
| f_geography_column | name | N/A | Yes |
| coord_dimension | integer | N/A | Yes |
| srid | integer | N/A | Yes |
| type | text | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE geography_columns
(
    f_table_catalog name NULL,
    f_table_schema name NULL,
    f_table_name name NULL,
    f_geography_column name NULL,
    coord_dimension integer NULL,
    srid integer NULL,
    type text NULL
);

```

## Table: geometry_columns

Total rows: 3

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| f_table_catalog | character varying | 256 | Yes |
| f_table_schema | name | N/A | Yes |
| f_table_name | name | N/A | Yes |
| f_geometry_column | name | N/A | Yes |
| coord_dimension | integer | N/A | Yes |
| srid | integer | N/A | Yes |
| type | character varying | 30 | Yes |

### Create Table Statement

```sql
CREATE TABLE geometry_columns
(
    f_table_catalog character varying(256) NULL,
    f_table_schema name NULL,
    f_table_name name NULL,
    f_geometry_column name NULL,
    coord_dimension integer NULL,
    srid integer NULL,
    type character varying(30) NULL
);

```

### Sample Data

| f\_table\_catalog | f\_table\_schema | f\_table\_name | f\_geometry\_column | coord\_dimension | srid | type |
| --- | --- | --- | --- | --- | --- | --- |
| opennem | public | location | boundary | 2 | 4326 | POLYGON |
| opennem | public | bom\_station | geom | 2 | 4326 | POINT |
| opennem | public | location | geom | 2 | 4326 | POINT |

## Table: location

Total rows: 551

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| id | integer | N/A | No |
| address1 | text | N/A | Yes |
| address2 | text | N/A | Yes |
| locality | text | N/A | Yes |
| state | text | N/A | Yes |
| postcode | text | N/A | Yes |
| place_id | text | N/A | Yes |
| geocode_approved | boolean | N/A | Yes |
| geocode_skip | boolean | N/A | Yes |
| geocode_processed_at | timestamp without time zone | N/A | Yes |
| geocode_by | text | N/A | Yes |
| geom | USER-DEFINED | N/A | Yes |
| osm_way_id | text | N/A | Yes |
| boundary | USER-DEFINED | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE location
(
    id integer NOT NULL,
    address1 text NULL,
    address2 text NULL,
    locality text NULL,
    state text NULL,
    postcode text NULL,
    place_id text NULL,
    geocode_approved boolean NULL,
    geocode_skip boolean NULL,
    geocode_processed_at timestamp without time zone NULL,
    geocode_by text NULL,
    geom geometry(Point,4326) NULL,
    osm_way_id text NULL,
    boundary geometry(Polygon,4326) NULL
);

```

### Constraints

- PRIMARY KEY (id)

### Indexes

- CREATE UNIQUE INDEX location_pkey ON public.location USING btree (id)
- CREATE INDEX idx_location_boundary ON public.location USING gist (boundary)
- CREATE INDEX idx_location_geom ON public.location USING gist (geom)
- CREATE INDEX ix_location_place_id ON public.location USING btree (place_id)

### Sample Data

| id | address1 | address2 | locality | state | postcode | place\_id | geocode\_approved | geocode\_skip | geocode\_processed\_at | geocode\_by | geom | osm\_way\_id | boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 420 | None | None | Crudine | NSW | None | None | False | False | None | None | 0101000020E6100000D7E9CCD903BA6240159E6E13B06E40C0 | None | None |
| 13753 |  |  |  | QLD | None | None | True | False | None | opennem\.registry | 0101000020E61000006CD097DE7E136340634337FB03653BC0 | None | None |
| 13752 |  |  |  | QLD | None | None | True | False | None | opennem\.registry | 0101000020E6100000C2ADA84E3C14634058088B0E4A5F3BC0 | None | None |
| 821 | None | None | Sladevale | QLD | 4370 | None | False | False | None | None | 0101000020E61000004DF4F92823026340D74CBED9E62E3CC0 | None | None |
| 13552 |  |  |  | NSW | None | None | True | False | None | opennem\.registry | 0101000020E6100000E3BF296EACAE62405EE3A0FEEF4F41C0 | None | None |

## Table: milestones

Total rows: 15,165

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| instance_id | uuid | N/A | No |
| record_id | text | N/A | No |
| interval | timestamp without time zone | N/A | No |
| significance | integer | N/A | No |
| value | double precision | N/A | No |
| network_id | text | N/A | Yes |
| fueltech_id | text | N/A | Yes |
| description | character varying | N/A | Yes |
| period | character varying | N/A | Yes |
| aggregate | character varying | N/A | No |
| metric | character varying | N/A | Yes |
| value_unit | character varying | N/A | Yes |
| description_long | character varying | N/A | Yes |
| network_region | text | N/A | Yes |
| previous_instance_id | uuid | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE milestones
(
    instance_id uuid NOT NULL,
    record_id text NOT NULL,
    interval timestamp without time zone NOT NULL,
    significance integer NOT NULL,
    value double precision NOT NULL,
    network_id text NULL,
    fueltech_id text NULL,
    description character varying NULL,
    period character varying NULL,
    aggregate character varying NOT NULL,
    metric character varying NULL,
    value_unit character varying NULL,
    description_long character varying NULL,
    network_region text NULL,
    previous_instance_id uuid NULL
);

```

### Constraints

- UNIQUE (record_id, "interval")
- FOREIGN KEY (network_id) REFERENCES network(code)
- PRIMARY KEY (record_id, "interval")

### Indexes

- CREATE UNIQUE INDEX excl_milestone_record_id_interval ON public.milestones USING btree (record_id, "interval")
- CREATE UNIQUE INDEX milestones_pkey ON public.milestones USING btree (record_id, "interval")
- CREATE INDEX idx_milestone_fueltech_id ON public.milestones USING btree (fueltech_id)
- CREATE INDEX idx_milestone_network_id ON public.milestones USING btree (network_id)
- CREATE INDEX ix_milestones_interval ON public.milestones USING btree ("interval")
- CREATE INDEX ix_milestones_record_id ON public.milestones USING btree (record_id)

### Sample Data

| instance\_id | record\_id | interval | significance | value | network\_id | fueltech\_id | description | period | aggregate | metric | value\_unit | description\_long | network\_region | previous\_instance\_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8ed371ed\-eb86\-4af5\-8869\-ff60fb560b77 | au\.nem\.nsw1\.solar\.energy\.day\.high | 2016\-09\-19 00:00:00 | 9 | 5162\.118 | NEM | solar | Daily solar energy high record for NEM in New South Wales | day | high | energy | MWh | None | NSW1 | e7e665cf\-4a35\-4b37\-8ddb\-bb9a697f2d09 |
| ad61d493\-4752\-423a\-b245\-0ab33fa9a090 | au\.nem\.battery\_charging\.energy\.quarter\.high | 2019\-04\-01 00:00:00 | 8 | 19645\.8565 | NEM | battery\_charging | Quarterly battery \(charging\) energy high record for NEM | quarter | high | energy | MWh | None | None | 22c97aad\-91bf\-4c65\-8266\-11640dba4e21 |
| 6c805795\-f018\-4ca8\-abfd\-3a92bed4ec12 | au\.nem\.solar\.energy\.day\.high | 2016\-08\-02 00:00:00 | 9 | 10071\.1865 | NEM | solar | Daily solar energy high record for NEM | day | high | energy | MWh | None | None | 10f71d5d\-1f3a\-4ded\-b91a\-6625762477f9 |
| 740b3c2e\-a052\-4ebc\-a223\-49a3bc828463 | au\.nem\.coal\.power\.interval\.low | 1998\-12\-08 02:45:00 | 4 | 14247\.88 | NEM | coal | Interval coal power low record for NEM | interval | low | power | MW | None | None | f1aeca8d\-1433\-4cae\-8210\-c347d5768c53 |
| 33b2ed33\-eb85\-401d\-a0ad\-8904a6c55408 | au\.nem\.demand\.interval\.high | 2007\-06\-20 03:30:00 | 5 | 32532\.95049 | NEM | demand | Interval demand high record for NEM | interval | high | demand | MW | None | None | a2033ac6\-448d\-488a\-8199\-461a7cbd282e |

## Table: mv_fueltech_daily

Total rows: 361,037

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| trading_day | timestamp without time zone | N/A | Yes |
| network_id | text | N/A | Yes |
| network_region | text | N/A | Yes |
| fueltech_code | text | N/A | Yes |
| generated | numeric | N/A | Yes |
| energy | numeric | N/A | Yes |
| emissions | numeric | N/A | Yes |
| emissions_intensity | numeric | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE mv_fueltech_daily
(
    trading_day timestamp without time zone NULL,
    network_id text NULL,
    network_region text NULL,
    fueltech_code text NULL,
    generated numeric NULL,
    energy numeric NULL,
    emissions numeric NULL,
    emissions_intensity numeric NULL
);

```

### Sample Data

| trading\_day | network\_id | network\_region | fueltech\_code | generated | energy | emissions | emissions\_intensity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2001\-11\-22 00:00:00 | NEM | QLD1 | coal\_black | 1459446\.6300 | 121595\.6667 | 116063\.3763 | 0\.9545 |
| 2022\-06\-26 00:00:00 | NEM | NSW1 | battery\_discharging | 1433\.3742 | 119\.6984 | 0\.0000 | 0\.0000 |
| 2013\-02\-17 00:00:00 | NEM | QLD1 | hydro | 25944\.6525 | 2162\.0494 | 0\.0000 | 0\.0000 |
| 2001\-02\-03 00:00:00 | NEM | VIC1 | gas\_ocgt | 1792\.4900 | 149\.3742 | 131\.3603 | 0\.8794 |
| 2013\-11\-21 00:00:00 | NEM | SA1 | gas\_ccgt | 120235\.3751 | 10019\.4655 | 5066\.8267 | 0\.5057 |

## Table: mv_weather_observations

Total rows: 5,409,699

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| observation_time | timestamp with time zone | N/A | Yes |
| station_id | text | N/A | Yes |
| temp_air | numeric | N/A | Yes |
| temp_min | numeric | N/A | Yes |
| temp_max | numeric | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE mv_weather_observations
(
    observation_time timestamp with time zone NULL,
    station_id text NULL,
    temp_air numeric NULL,
    temp_min numeric NULL,
    temp_max numeric NULL
);

```

### Sample Data

| observation\_time | station\_id | temp\_air | temp\_min | temp\_max |
| --- | --- | --- | --- | --- |
| 2021\-01\-21 23:00:00\+00:00 | 200601 | 25\.2000000000000000 | 25\.2 | 25\.2 |
| 2021\-02\-03 09:30:00\+00:00 | 015602 | 34\.3000000000000000 | 34\.3 | 34\.3 |
| 2021\-03\-07 20:00:00\+00:00 | 040211 | 21\.7000000000000000 | 21\.7 | 21\.7 |
| 2021\-04\-06 11:30:00\+00:00 | 014310 | 27\.5000000000000000 | 27\.5 | 27\.5 |
| 1892\-07\-21 12:00:00\+00:00 | 094029 | None | 2\.8 | 11\.1 |

## Table: network

Total rows: 7

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| created_by | text | N/A | Yes |
| created_at | timestamp with time zone | N/A | Yes |
| updated_at | timestamp with time zone | N/A | Yes |
| code | text | N/A | No |
| country | text | N/A | No |
| label | text | N/A | Yes |
| timezone | text | N/A | No |
| interval_size | integer | N/A | No |
| offset | integer | N/A | Yes |
| timezone_database | text | N/A | Yes |
| export_set | boolean | N/A | No |
| interval_shift | integer | N/A | No |
| network_price | text | N/A | No |
| data_start_date | timestamp with time zone | N/A | Yes |
| data_end_date | timestamp with time zone | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE network
(
    created_by text NULL,
    created_at timestamp with time zone NULL,
    updated_at timestamp with time zone NULL,
    code text NOT NULL,
    country text NOT NULL,
    label text NULL,
    timezone text NOT NULL,
    interval_size integer NOT NULL,
    offset integer NULL,
    timezone_database text NULL,
    export_set boolean NOT NULL,
    interval_shift integer NOT NULL,
    network_price text NOT NULL,
    data_start_date timestamp with time zone NULL,
    data_end_date timestamp with time zone NULL
);

```

### Constraints

- PRIMARY KEY (code)

### Indexes

- CREATE UNIQUE INDEX network_pkey ON public.network USING btree (code)
- CREATE INDEX idx_network_code ON public.network USING btree (code)
- CREATE INDEX ix_network_data_end_date ON public.network USING btree (data_end_date)
- CREATE INDEX ix_network_data_start_date ON public.network USING btree (data_start_date)

### Sample Data

| created\_by | created\_at | updated\_at | code | country | label | timezone | interval\_size | offset | timezone\_database | export\_set | interval\_shift | network\_price | data\_start\_date | data\_end\_date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| None | 2020\-12\-09 01:46:31\.176786\+00:00 | 2024\-08\-03 00:15:22\.319623\+00:00 | APVI | au | APVI | Australia/Perth | 15 | 600 | AWST | False | 0 | WEM | 2015\-03\-19 20:15:00\+00:00 | 2024\-08\-03 00:00:00\+00:00 |
| None | 2024\-08\-10 04:32:14\.380672\+00:00 | None | WEMDE | au | WEMDE | Australia/Perth | 5 | 480 | AWST | True | 0 | WEMDE | None | None |
| None | 2021\-04\-12 07:06:18\.835747\+00:00 | 2024\-08\-10 04:32:14\.674557\+00:00 | AEMO\_ROOFTOP\_BACKFILL | au | AEMO Rooftop Backfill | Australia/Brisbane | 30 | 600 | AEST | False | 0 | NEM | None | None |
| None | 2023\-02\-22 09:54:49\.679305\+00:00 | 2024\-08\-10 04:32:14\.781558\+00:00 | OPENNEM\_ROOFTOP\_BACKFILL | au | OpenNEM Rooftop Backfill | Australia/Brisbane | 30 | 600 | AEST | False | 0 | NEM | 2015\-03\-19 20:15:00\+00:00 | 2018\-02\-28 09:30:00\+00:00 |
| None | 2020\-12\-09 01:46:31\.118850\+00:00 | 2024\-08\-02 04:15:22\.375279\+00:00 | WEM | au | WEM | Australia/Perth | 30 | 480 | AWST | True | 0 | WEM | 2006\-09\-19 16:00:00\+00:00 | 2024\-08\-01 23:55:00\+00:00 |

## Table: network_region

Total rows: 12

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| created_by | text | N/A | Yes |
| created_at | timestamp with time zone | N/A | Yes |
| updated_at | timestamp with time zone | N/A | Yes |
| network_id | text | N/A | No |
| code | text | N/A | No |
| timezone | text | N/A | Yes |
| timezone_database | text | N/A | Yes |
| offset | integer | N/A | Yes |
| export_set | boolean | N/A | No |

### Create Table Statement

```sql
CREATE TABLE network_region
(
    created_by text NULL,
    created_at timestamp with time zone NULL,
    updated_at timestamp with time zone NULL,
    network_id text NOT NULL,
    code text NOT NULL,
    timezone text NULL,
    timezone_database text NULL,
    offset integer NULL,
    export_set boolean NOT NULL
);

```

### Constraints

- FOREIGN KEY (network_id) REFERENCES network(code)
- PRIMARY KEY (network_id, code)

### Indexes

- CREATE UNIQUE INDEX network_region_pkey ON public.network_region USING btree (network_id, code)

### Sample Data

| created\_by | created\_at | updated\_at | network\_id | code | timezone | timezone\_database | offset | export\_set |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| None | 2020\-12\-09 01:46:31\.540863\+00:00 | None | NEM | SA1 | None | None | None | True |
| None | 2021\-04\-09 10:15:56\.445329\+00:00 | None | AEMO\_ROOFTOP | TAS1 | None | None | None | True |
| None | 2024\-08\-10 04:32:14\.952549\+00:00 | None | WEM | WEMDE | None | None | None | True |
| None | 2021\-04\-09 10:15:56\.438248\+00:00 | None | AEMO\_ROOFTOP | QLD1 | None | None | None | True |
| None | 2021\-04\-09 10:15:56\.432350\+00:00 | None | AEMO\_ROOFTOP | NSW1 | None | None | None | True |

## Table: participant

Total rows: 201

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| participantid | character varying | 10 | No |
| participantclassid | character varying | 20 | Yes |
| name | character varying | 80 | Yes |
| id | integer | N/A | No |
| description | character varying | 64 | Yes |
| code | text | N/A | Yes |
| acn | character varying | 9 | Yes |
| primarybusiness | character varying | 40 | Yes |
| name | text | N/A | Yes |
| lastchanged | timestamp without time zone | N/A | Yes |
| network_name | text | N/A | Yes |
| network_code | text | N/A | Yes |
| country | text | N/A | Yes |
| abn | text | N/A | Yes |
| approved | boolean | N/A | Yes |
| approved_by | text | N/A | Yes |
| approved_at | timestamp with time zone | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE participant
(
    participantid character varying(10) NOT NULL,
    participantclassid character varying(20) NULL,
    name character varying(80) NULL,
    id integer NOT NULL,
    description character varying(64) NULL,
    code text NULL,
    acn character varying(9) NULL,
    primarybusiness character varying(40) NULL,
    name text NULL,
    lastchanged timestamp(3) without time zone NULL,
    network_name text NULL,
    network_code text NULL,
    country text NULL,
    abn text NULL,
    approved boolean NULL,
    approved_by text NULL,
    approved_at timestamp with time zone NULL
);

```

### Constraints

- PRIMARY KEY (id)

### Indexes

- CREATE UNIQUE INDEX participant_pkey ON public.participant USING btree (id)
- CREATE UNIQUE INDEX ix_participant_code ON public.participant USING btree (code)

### Sample Data

| participantid | participantclassid | name | id | description | code | acn | primarybusiness | name | lastchanged | network\_name | network\_code | country | abn | approved | approved\_by | approved\_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 195 | Wenergy | WesternEnergy | None | None | None | None | False | None | None |
| 88 | Ader | AdvancedEnergyResources | None | None | None | None | False | None | None |
| 83 | WALKAWAY | WalkawayWindPowerPty | None | None | None | None | False | None | None |
| 81 | UON | UONPty | None | None | None | None | False | None | None |
| 38 | AMENERGY | AmandaEnergyPtyLt | None | None | None | None | False | None | None |

## Table: pg_stat_statements

Total rows: 163

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| userid | oid | N/A | Yes |
| dbid | oid | N/A | Yes |
| toplevel | boolean | N/A | Yes |
| queryid | bigint | N/A | Yes |
| query | text | N/A | Yes |
| plans | bigint | N/A | Yes |
| total_plan_time | double precision | N/A | Yes |
| min_plan_time | double precision | N/A | Yes |
| max_plan_time | double precision | N/A | Yes |
| mean_plan_time | double precision | N/A | Yes |
| stddev_plan_time | double precision | N/A | Yes |
| calls | bigint | N/A | Yes |
| total_exec_time | double precision | N/A | Yes |
| min_exec_time | double precision | N/A | Yes |
| max_exec_time | double precision | N/A | Yes |
| mean_exec_time | double precision | N/A | Yes |
| stddev_exec_time | double precision | N/A | Yes |
| rows | bigint | N/A | Yes |
| shared_blks_hit | bigint | N/A | Yes |
| shared_blks_read | bigint | N/A | Yes |
| shared_blks_dirtied | bigint | N/A | Yes |
| shared_blks_written | bigint | N/A | Yes |
| local_blks_hit | bigint | N/A | Yes |
| local_blks_read | bigint | N/A | Yes |
| local_blks_dirtied | bigint | N/A | Yes |
| local_blks_written | bigint | N/A | Yes |
| temp_blks_read | bigint | N/A | Yes |
| temp_blks_written | bigint | N/A | Yes |
| blk_read_time | double precision | N/A | Yes |
| blk_write_time | double precision | N/A | Yes |
| wal_records | bigint | N/A | Yes |
| wal_fpi | bigint | N/A | Yes |
| wal_bytes | numeric | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE pg_stat_statements
(
    userid oid NULL,
    dbid oid NULL,
    toplevel boolean NULL,
    queryid bigint NULL,
    query text NULL,
    plans bigint NULL,
    total_plan_time double precision NULL,
    min_plan_time double precision NULL,
    max_plan_time double precision NULL,
    mean_plan_time double precision NULL,
    stddev_plan_time double precision NULL,
    calls bigint NULL,
    total_exec_time double precision NULL,
    min_exec_time double precision NULL,
    max_exec_time double precision NULL,
    mean_exec_time double precision NULL,
    stddev_exec_time double precision NULL,
    rows bigint NULL,
    shared_blks_hit bigint NULL,
    shared_blks_read bigint NULL,
    shared_blks_dirtied bigint NULL,
    shared_blks_written bigint NULL,
    local_blks_hit bigint NULL,
    local_blks_read bigint NULL,
    local_blks_dirtied bigint NULL,
    local_blks_written bigint NULL,
    temp_blks_read bigint NULL,
    temp_blks_written bigint NULL,
    blk_read_time double precision NULL,
    blk_write_time double precision NULL,
    wal_records bigint NULL,
    wal_fpi bigint NULL,
    wal_bytes numeric NULL
);

```

### Sample Data

| userid | dbid | toplevel | queryid | query | plans | total\_plan\_time | min\_plan\_time | max\_plan\_time | mean\_plan\_time | stddev\_plan\_time | calls | total\_exec\_time | min\_exec\_time | max\_exec\_time | mean\_exec\_time | stddev\_exec\_time | rows | shared\_blks\_hit | shared\_blks\_read | shared\_blks\_dirtied | shared\_blks\_written | local\_blks\_hit | local\_blks\_read | local\_blks\_dirtied | local\_blks\_written | temp\_blks\_read | temp\_blks\_written | blk\_read\_time | blk\_write\_time | wal\_records | wal\_fpi | wal\_bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 16384 | 16448 | True | \-8731996797557825404 | SELECT \* FROM geography\_columns ORDER BY RANDOM\(\) LIMIT $1 | 0 | 0\.0 | 0\.0 | 0\.0 | 0\.0 | 0\.0 | 4 | 688\.0327880000001 | 147\.474185 | 194\.75837700000002 | 172\.008197 | 19\.165036866190693 | 0 | 1024013 | 69 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0\.0 | 0\.0 | 0 | 0 | 0 |
| 16384 | 16448 | True | 9011935193094275261 | SELECT COUNT\(\*\) FROM mv\_weather\_observations | 0 | 0\.0 | 0\.0 | 0\.0 | 0\.0 | 0\.0 | 6 | 5364\.983437000001 | 858\.454051 | 952\.635073 | 894\.1639061666667 | 29\.27090554208975 | 6 | 77 | 70949 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0\.0 | 0\.0 | 0 | 0 | 0 |
| 16384 | 16448 | True | \-3249962036932894869 | CREATE TEMP TABLE \_\_tmp\_facility\_scada\_20240909230545
    \(LIKE facility\_scada INCLUDING DEFAULTS\)
    ON COMMIT DROP | 0 | 0\.0 | 0\.0 | 0\.0 | 0\.0 | 0\.0 | 1 | 49\.406877 | 49\.406877 | 49\.406877 | 49\.406877 | 0\.0 | 0 | 522 | 96 | 29 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0\.0 | 0\.0 | 106 | 27 | 165680 |
| 16384 | 16448 | True | \-5095182691218548825 | SELECT COUNT\(\*\) FROM raster\_columns | 0 | 0\.0 | 0\.0 | 0\.0 | 0\.0 | 0\.0 | 5 | 374\.84682 | 69\.52842 | 78\.197919 | 74\.969364 | 2\.971104748325582 | 5 | 67753 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0\.0 | 0\.0 | 0 | 0 | 0 |
| 16384 | 16448 | True | \-8033802810445564974 | SELECT \* FROM mv\_weather\_observations ORDER BY RANDOM\(\) LIMIT $1 | 0 | 0\.0 | 0\.0 | 0\.0 | 0\.0 | 0\.0 | 4 | 7378\.967586 | 1806\.7550939999999 | 1886\.119971 | 1844\.7418965 | 28\.33082262714134 | 20 | 27744 | 150800 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0\.0 | 0\.0 | 0 | 0 | 0 |

## Table: pg_stat_statements_info

Total rows: 1

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| dealloc | bigint | N/A | Yes |
| stats_reset | timestamp with time zone | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE pg_stat_statements_info
(
    dealloc bigint NULL,
    stats_reset timestamp with time zone NULL
);

```

### Sample Data

| dealloc | stats\_reset |
| --- | --- |
| 0 | 2024\-09\-09 22:19:07\.454676\+00:00 |

## Table: raster_columns

Total rows: 0

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| r_table_catalog | name | N/A | Yes |
| r_table_schema | name | N/A | Yes |
| r_table_name | name | N/A | Yes |
| r_raster_column | name | N/A | Yes |
| srid | integer | N/A | Yes |
| scale_x | double precision | N/A | Yes |
| scale_y | double precision | N/A | Yes |
| blocksize_x | integer | N/A | Yes |
| blocksize_y | integer | N/A | Yes |
| same_alignment | boolean | N/A | Yes |
| regular_blocking | boolean | N/A | Yes |
| num_bands | integer | N/A | Yes |
| pixel_types | ARRAY | N/A | Yes |
| nodata_values | ARRAY | N/A | Yes |
| out_db | ARRAY | N/A | Yes |
| extent | USER-DEFINED | N/A | Yes |
| spatial_index | boolean | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE raster_columns
(
    r_table_catalog name NULL,
    r_table_schema name NULL,
    r_table_name name NULL,
    r_raster_column name NULL,
    srid integer NULL,
    scale_x double precision NULL,
    scale_y double precision NULL,
    blocksize_x integer NULL,
    blocksize_y integer NULL,
    same_alignment boolean NULL,
    regular_blocking boolean NULL,
    num_bands integer NULL,
    pixel_types text[] NULL,
    nodata_values double precision[] NULL,
    out_db boolean[] NULL,
    extent geometry NULL,
    spatial_index boolean NULL
);

```

## Table: raster_overviews

Total rows: 0

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| o_table_catalog | name | N/A | Yes |
| o_table_schema | name | N/A | Yes |
| o_table_name | name | N/A | Yes |
| o_raster_column | name | N/A | Yes |
| r_table_catalog | name | N/A | Yes |
| r_table_schema | name | N/A | Yes |
| r_table_name | name | N/A | Yes |
| r_raster_column | name | N/A | Yes |
| overview_factor | integer | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE raster_overviews
(
    o_table_catalog name NULL,
    o_table_schema name NULL,
    o_table_name name NULL,
    o_raster_column name NULL,
    r_table_catalog name NULL,
    r_table_schema name NULL,
    r_table_name name NULL,
    r_raster_column name NULL,
    overview_factor integer NULL
);

```

## Table: spatial_ref_sys

Total rows: 8,500

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| srid | integer | N/A | No |
| auth_name | character varying | 256 | Yes |
| auth_srid | integer | N/A | Yes |
| srtext | character varying | 2048 | Yes |
| proj4text | character varying | 2048 | Yes |

### Create Table Statement

```sql
CREATE TABLE spatial_ref_sys
(
    srid integer NOT NULL,
    auth_name character varying(256) NULL,
    auth_srid integer NULL,
    srtext character varying(2048) NULL,
    proj4text character varying(2048) NULL
);

```

### Constraints

- PRIMARY KEY (srid)
- CHECK (((srid > 0) AND (srid <= 998999)))

### Indexes

- CREATE UNIQUE INDEX spatial_ref_sys_pkey ON public.spatial_ref_sys USING btree (srid)

### Sample Data

| srid | auth\_name | auth\_srid | srtext | proj4text |
| --- | --- | --- | --- | --- |
| 3732 | EPSG | 3732 | PROJCS\["NAD83\(NSRS2007\) / Wyoming West Central \(ftUS\)",GEOGCS\["NAD83\(NSRS2007\)",DATUM\["NAD83\_National\_Spatial\_Reference\_System\_2007",SPHEROID\["GRS 1980",6378137,298\.257222101,AUTHORITY\["EPSG","7019"\]\]\.\.\. | \+proj=tmerc \+lat\_0=40\.5 \+lon\_0=\-108\.75 \+k=0\.9999375 \+x\_0=600000 \+y\_0=0 \+ellps=GRS80 \+towgs84=0,0,0,0,0,0,0 \+units=us\-ft \+no\_defs  |
| 103003 | ESRI | 103003 | PROJCS\["NAD\_1983\_2011\_StatePlane\_California\_I\_FIPS\_0401\_Ft\_US \(deprecated\)",GEOGCS\["NAD83\(2011\)",DATUM\["NAD83\_National\_Spatial\_Reference\_System\_2011",SPHEROID\["GRS 1980",6378137,298\.257222101,AUTHORIT\.\.\. | \+proj=lcc \+lat\_0=39\.3333333333333 \+lon\_0=\-122 \+lat\_1=40 \+lat\_2=41\.6666666666667 \+x\_0=2000000 \+y\_0=500000 \+ellps=GRS80 \+units=us\-ft \+no\_defs |
| 103507 | ESRI | 103507 | PROJCS\["NAD\_1983\_CORS96\_StatePlane\_Ohio\_South\_FIPS\_3402",GEOGCS\["NAD83\(CORS96\)",DATUM\["NAD83\_Continuously\_Operating\_Reference\_Station\_1996",SPHEROID\["GRS 1980",6378137,298\.257222101,AUTHORITY\["EPSG","\.\.\. | \+proj=lcc \+lat\_0=38 \+lon\_0=\-82\.5 \+lat\_1=38\.7333333333333 \+lat\_2=40\.0333333333333 \+x\_0=600000 \+y\_0=0 \+ellps=GRS80 \+units=m \+no\_defs |
| 4978 | EPSG | 4978 | GEOCCS\["WGS 84",DATUM\["WGS\_1984",SPHEROID\["WGS 84",6378137,298\.257223563,AUTHORITY\["EPSG","7030"\]\],AUTHORITY\["EPSG","6326"\]\],PRIMEM\["Greenwich",0,AUTHORITY\["EPSG","8901"\]\],UNIT\["metre",1,AUTHORITY\["EP\.\.\. | \+proj=geocent \+datum=WGS84 \+units=m \+no\_defs  |
| 3687 | EPSG | 3687 | PROJCS\["NAD83\(NSRS2007\) / Virginia South",GEOGCS\["NAD83\(NSRS2007\)",DATUM\["NAD83\_National\_Spatial\_Reference\_System\_2007",SPHEROID\["GRS 1980",6378137,298\.257222101,AUTHORITY\["EPSG","7019"\]\],TOWGS84\[0,0,\.\.\. | \+proj=lcc \+lat\_1=37\.96666666666667 \+lat\_2=36\.76666666666667 \+lat\_0=36\.33333333333334 \+lon\_0=\-78\.5 \+x\_0=3500000 \+y\_0=1000000 \+ellps=GRS80 \+towgs84=0,0,0,0,0,0,0 \+units=m \+no\_defs  |

## Table: station

Total rows: 551

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| created_by | text | N/A | Yes |
| stationid | character varying | 10 | No |
| created_at | timestamp with time zone | N/A | Yes |
| stationname | character varying | 80 | Yes |
| address1 | character varying | 80 | Yes |
| updated_at | timestamp with time zone | N/A | Yes |
| address2 | character varying | 80 | Yes |
| id | integer | N/A | No |
| address3 | character varying | 80 | Yes |
| participant_id | integer | N/A | Yes |
| address4 | character varying | 80 | Yes |
| location_id | integer | N/A | Yes |
| code | text | N/A | No |
| city | character varying | 40 | Yes |
| state | character varying | 10 | Yes |
| name | text | N/A | Yes |
| description | text | N/A | Yes |
| postcode | character varying | 10 | Yes |
| lastchanged | timestamp without time zone | N/A | Yes |
| wikipedia_link | text | N/A | Yes |
| connectionpointid | character varying | 10 | Yes |
| wikidata_id | text | N/A | Yes |
| network_code | text | N/A | Yes |
| network_name | text | N/A | Yes |
| approved | boolean | N/A | Yes |
| approved_by | text | N/A | Yes |
| approved_at | timestamp with time zone | N/A | Yes |
| website_url | text | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE station
(
    created_by text NULL,
    stationid character varying(10) NOT NULL,
    created_at timestamp with time zone NULL,
    stationname character varying(80) NULL,
    address1 character varying(80) NULL,
    updated_at timestamp with time zone NULL,
    address2 character varying(80) NULL,
    id integer NOT NULL,
    address3 character varying(80) NULL,
    participant_id integer NULL,
    address4 character varying(80) NULL,
    location_id integer NULL,
    code text NOT NULL,
    city character varying(40) NULL,
    state character varying(10) NULL,
    name text NULL,
    description text NULL,
    postcode character varying(10) NULL,
    lastchanged timestamp(3) without time zone NULL,
    wikipedia_link text NULL,
    connectionpointid character varying(10) NULL,
    wikidata_id text NULL,
    network_code text NULL,
    network_name text NULL,
    approved boolean NULL,
    approved_by text NULL,
    approved_at timestamp with time zone NULL,
    website_url text NULL
);

```

### Constraints

- UNIQUE (code)
- FOREIGN KEY (location_id) REFERENCES location(id)
- FOREIGN KEY (participant_id) REFERENCES participant(id)
- PRIMARY KEY (id)

### Indexes

- CREATE UNIQUE INDEX excl_station_network_duid ON public.station USING btree (code)
- CREATE UNIQUE INDEX station_pkey ON public.station USING btree (id)
- CREATE UNIQUE INDEX ix_station_code ON public.station USING btree (code)
- CREATE INDEX ix_station_network_code ON public.station USING btree (network_code)

### Sample Data

| created\_by | stationid | created\_at | stationname | address1 | updated\_at | address2 | id | address3 | participant\_id | address4 | location\_id | code | city | state | name | description | postcode | lastchanged | wikipedia\_link | connectionpointid | wikidata\_id | network\_code | network\_name | approved | approved\_by | approved\_at | website\_url |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| opennem\.registry | 2020\-12\-09 15:32:39\.826093\+00:00 | 2024\-06\-07 13:11:30\.193633\+00:00 | 280 | None | 13695 | SNOWY6 | Blowering | None | None | None | None | Blowering | True | opennem\.importer\.facilities | 2024\-06\-07 23:11:30\.236607\+00:00 | None |
| opennem\.registry | 2020\-12\-09 15:32:39\.826093\+00:00 | 2024\-06\-07 13:12:24\.478294\+00:00 | 269 | None | 13684 | SHEP1 | Shepparton | None | None | None | None | Shepparton Wastewater Treatment | True | opennem\.importer\.facilities | 2024\-06\-07 23:12:24\.524195\+00:00 | None |
| opennem\.registry | 2020\-12\-09 15:32:39\.826093\+00:00 | 2024\-06\-07 13:12:24\.816037\+00:00 | 292 | None | 13707 | SVALE | Springvale | None | None | None | None | Springvale | True | opennem\.importer\.facilities | 2024\-06\-07 23:12:24\.859488\+00:00 | None |
| opennem\.init | 2021\-07\-27 06:53:05\.835973\+00:00 | 2024\-06\-07 13:11:30\.868222\+00:00 | 502 | None | 13796 | SUNTPSF | Suntop | Suntop Solar Farm is located near Wellington, south of Dubbo in regional New South Wales\. The site will accommodate a large\-scale solar PV system utilising single\-axis tracking, and ground mounted pan\.\.\. | None | None | None | Suntop Solar Farm | True | opennem\.importer\.facilities | 2024\-06\-07 23:11:30\.913872\+00:00 | https://suntopsolarfarm\.com\.au/ |
| opennem\.registry | 2020\-12\-09 15:32:39\.826093\+00:00 | 2024\-06\-07 13:12:17\.573717\+00:00 | 128 | None | 13543 | GLENMAGG | Glenmaggie | None | None | None | None | Glenmaggie | True | opennem\.importer\.facilities | 2024\-06\-07 23:12:17\.616190\+00:00 | None |

## Table: stats

Total rows: 403

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| created_by | text | N/A | Yes |
| created_at | timestamp with time zone | N/A | Yes |
| updated_at | timestamp with time zone | N/A | Yes |
| stat_date | timestamp with time zone | N/A | No |
| country | text | N/A | No |
| stat_type | text | N/A | No |
| value | numeric | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE stats
(
    created_by text NULL,
    created_at timestamp with time zone NULL,
    updated_at timestamp with time zone NULL,
    stat_date timestamp with time zone NOT NULL,
    country text NOT NULL,
    stat_type text NOT NULL,
    value numeric NULL
);

```

### Constraints

- PRIMARY KEY (stat_date, country, stat_type)

### Indexes

- CREATE UNIQUE INDEX stats_pkey ON public.stats USING btree (stat_date, country, stat_type)
- CREATE INDEX ix_stats_stat_date ON public.stats USING btree (stat_date)

### Sample Data

| created\_by | created\_at | updated\_at | stat\_date | country | stat\_type | value |
| --- | --- | --- | --- | --- | --- | --- |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 2001\-03\-31 00:00:00\+00:00 | au | CPI | 73\.9 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 2018\-06\-30 00:00:00\+00:00 | au | CPI | 113\.0 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 2012\-09\-30 00:00:00\+00:00 | au | CPI | 101\.8 |
| None | 2023\-02\-24 11:31:40\.797370\+00:00 | None | 2022\-06\-30 00:00:00\+00:00 | au | CPI | 126\.1 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 2019\-06\-30 00:00:00\+00:00 | au | CPI | 114\.8 |

## Table: task_profile

Total rows: 568,157

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| id | uuid | N/A | No |
| task_name | text | N/A | No |
| time_start | timestamp with time zone | N/A | No |
| time_end | timestamp with time zone | N/A | Yes |
| time_sql | timestamp with time zone | N/A | Yes |
| time_cpu | timestamp with time zone | N/A | Yes |
| errors | integer | N/A | No |
| retention_period | text | N/A | Yes |
| level | text | N/A | Yes |
| invokee_name | text | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE task_profile
(
    id uuid NOT NULL,
    task_name text NOT NULL,
    time_start timestamp with time zone NOT NULL,
    time_end timestamp with time zone NULL,
    time_sql timestamp with time zone NULL,
    time_cpu timestamp with time zone NULL,
    errors integer NOT NULL,
    retention_period text NULL,
    level text NULL,
    invokee_name text NULL
);

```

### Constraints

- PRIMARY KEY (id)

### Indexes

- CREATE UNIQUE INDEX task_profile_pkey ON public.task_profile USING btree (id)
- CREATE INDEX ix_task_profile_invokee_name ON public.task_profile USING btree (invokee_name)
- CREATE INDEX ix_task_profile_level ON public.task_profile USING btree (level)
- CREATE INDEX ix_task_profile_retention_period ON public.task_profile USING btree (retention_period)

### Sample Data

| id | task\_name | time\_start | time\_end | time\_sql | time\_cpu | errors | retention\_period | level | invokee\_name |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2eae5b02\-ed22\-47d0\-8a34\-b6b437df75b9 | run\_network\_data\_range\_update | 2024\-07\-09 23:15:56\.537659\+00:00 | 2024\-07\-09 23:15:56\.944615\+00:00 | None | None | 0 | forever | noisy |  |
| efda8724\-8fea\-4917\-ad97\-db71fac7179b | wem\_per\_interval\_check | 2024\-02\-22 18:44:32\.441682\+00:00 | 2024\-02\-22 18:44:52\.872327\+00:00 | None | None | 0 | forever | noisy |  |
| 09478283\-d2a3\-444a\-b0fc\-0e7dbc90c4fb | run\_flows\_for\_last\_intervals | 2024\-04\-22 01:05:00\.980012\+00:00 | 2024\-04\-22 01:05:01\.887607\+00:00 | None | None | 0 | forever | info |  |
| d8b99746\-f655\-4b74\-a5e4\-e5fdaf336657 | wem\_per\_interval\_check | 2024\-07\-02 04:18:13\.129430\+00:00 | 2024\-07\-02 04:18:26\.957180\+00:00 | None | None | 0 | forever | noisy |  |
| 9c5a2627\-1c24\-482f\-ae8f\-dcdbe9b49fbf | wem\_per\_interval\_check | 2024\-04\-24 16:14:43\.434559\+00:00 | 2024\-04\-24 16:15:01\.246845\+00:00 | None | None | 0 | forever | noisy |  |
