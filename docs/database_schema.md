# Database Schema

Database: opennem
PostgreSQL version: PostgreSQL 16.4 (Ubuntu 16.4-1.pgdg22.04+1) on x86_64-pc-linux-gnu, compiled by gcc (Ubuntu 11.4.0-1ubuntu1~22.04) 11.4.0, 64-bit
Schemas: public

## Table of Contents

| Schema | Table Name | Row Count |
|--------|------------|----------|
| public | [aemo_facility_data](#public-aemo-facility-data) | 0 |
| public | [aemo_market_notices](#public-aemo-market-notices) | 867 |
| public | [alembic_version](#public-alembic-version) | 1 |
| public | [api_keys](#public-api-keys) | 1 |
| public | [at_facility_daily](#public-at-facility-daily) | 2,885,368 |
| public | [at_network_demand](#public-at-network-demand) | 62,753 |
| public | [at_network_flows](#public-at-network-flows) | 7,917,760 |
| public | [at_network_flows_v3](#public-at-network-flows-v3) | 0 |
| public | [balancing_summary](#public-balancing-summary) | 11,329,360 |
| public | [bom_observation](#public-bom-observation) | 5,920,234 |
| public | [bom_station](#public-bom-station) | 773 |
| public | [crawl_history](#public-crawl-history) | 791,722 |
| public | [crawl_meta](#public-crawl-meta) | 50 |
| public | [facility](#public-facility) | 787 |
| public | [facility_scada](#public-facility-scada) | 769,756,781 |
| public | [facility_status](#public-facility-status) | 12 |
| public | [feedback](#public-feedback) | 94 |
| public | [fueltech](#public-fueltech) | 26 |
| public | [fueltech_group](#public-fueltech-group) | 10 |
| public | [location](#public-location) | 551 |
| public | [milestones](#public-milestones) | 18,741 |
| public | [network](#public-network) | 7 |
| public | [network_region](#public-network-region) | 12 |
| public | [participant](#public-participant) | 201 |
| public | [station](#public-station) | 551 |
| public | [stats](#public-stats) | 403 |
| public | [task_profile](#public-task-profile) | 568,157 |

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

## Table: public.aemo_facility_data

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
CREATE TABLE public.aemo_facility_data
(
    aemo_source USER-DEFINED NOT NULL,
    source_date date NOT NULL,
    name text,
    name_network text,
    network_region text,
    fueltech_id text,
    status_id text,
    duid text,
    units_no integer,
    capacity_registered numeric,
    closure_year_expected integer
);

```

### Constraints

- PRIMARY KEY (aemo_source, source_date)

### Indexes

- CREATE UNIQUE INDEX aemo_facility_data_pkey ON public.aemo_facility_data USING btree (aemo_source, source_date)

## Table: public.aemo_market_notices

Total rows: 867

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
CREATE TABLE public.aemo_market_notices
(
    notice_id integer NOT NULL,
    notice_type character varying NOT NULL,
    creation_date timestamp without time zone NOT NULL,
    issue_date timestamp without time zone NOT NULL,
    external_reference text,
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
| 117687 | NON\-CONFORMANCE | 2024\-08\-15 18:15:18 | 2024\-08\-15 18:15:00 | NON\-CONFORMANCE Region QLD1 Thursday, 15 August 2024 | AEMO ELECTRICITY MARKET NOTICE

NON\-CONFORMANCE QLD1 Region Thursday, 15 August 2024

AEMO has declared the following unit as non\-conforming under clause 3\.8\.23 of the National Electricity Rules:

Uni\.\.\. |
| 118023 | RECLASSIFY CONTINGENCY | 2024\-09\-01 07:39:09 | 2024\-09\-01 00:00:00 | Cancellation of a Non\-Credible Contingency Event: Farrell\-John Butters line and Farrell\-Rosebery\-Newton\-Queenstown line in TAS1 due to Lightning\. | Cancellation of reclassification of a Non\-Credible Contingency Event as a Credible Contingency Event due to Lightning\. AEMO considers the simultaneous trip of the following circuits is no longer reaso\.\.\. |
| 118105 | PRICES UNCHANGED | 2024\-09\-03 14:44:10 | 2024\-09\-03 00:00:00 | \[EventId:202409031435\_confirmed\] Prices for interval 03\-Sep\-2024 14:35 are now confirmed | AEMO ELECTRICITY MARKET NOTICE

Issued by Australian Energy Market Operator Ltd at 1440 hrs on 3 September 2024

PRICES ARE NOW CONFIRMED for trading interval 03\-Sep\-2024 14:35\.

In accordance with Ma\.\.\. |
| 118109 | MARKET SYSTEMS | 2024\-09\-03 16:42:16 | 2024\-09\-03 00:00:00 | CHG0097010 \| Production \| AEMO will be undertaking maintenance activities on the RCM system | Change Number: CHG0097010

Notification issued to: Market Notice

Notification Type: Initial

Change Type: Normal 

Service/ Component: Cohesity

Change Title: AEMO will be undertaking maintenance act\.\.\. |
| 117867 | PRICES UNCHANGED | 2024\-08\-27 13:36:42 | 2024\-08\-27 00:00:00 | \[EventId:202408271325\_confirmed\] Prices for interval 27\-Aug\-2024 13:25 are now confirmed | AEMO ELECTRICITY MARKET NOTICE

Issued by Australian Energy Market Operator Ltd at 1335 hrs on 27 August 2024

PRICES ARE NOW CONFIRMED for trading interval 27\-Aug\-2024 13:25\.

In accordance with Mark\.\.\. |

## Table: public.alembic_version

Total rows: 1

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| version_num | character varying | 32 | No |

### Create Table Statement

```sql
CREATE TABLE public.alembic_version
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

## Table: public.api_keys

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
CREATE TABLE public.api_keys
(
    keyid text NOT NULL,
    description text,
    revoked boolean NOT NULL,
    created_at timestamp with time zone
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

## Table: public.at_facility_daily

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
CREATE TABLE public.at_facility_daily
(
    trading_day timestamp with time zone NOT NULL,
    network_id text NOT NULL,
    facility_code text NOT NULL,
    fueltech_id text,
    energy numeric,
    market_value numeric,
    emissions numeric,
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
| 2012\-02\-07 00:00:00\+00:00 | NEM | ROMA\_7 | gas\_ocgt | 167\.2655299999999952 | 4926\.323535347620677392730 | 126\.53945113075199636871168 | QLD1 |
| 2019\-08\-16 00:00:00\+00:00 | NEM | TORRA4 | gas\_steam | 0 | 0 | 0 | SA1 |
| 2016\-01\-10 00:00:00\+00:00 | NEM | JLA02 | gas\_ocgt | 0 | 0 | 0 | VIC1 |
| 2021\-06\-06 00:00:00\+00:00 | NEM | TARONG\#4 | coal\_black | 8179\.37933083333363 | 714210\.0891055784147961060 | 7127\.9901333417805251993728 | QLD1 |
| 1998\-05\-10 00:00:00\+00:00 | NEM | EILDON2 | hydro | 0 | 0 | 0 | VIC1 |

## Table: public.at_network_demand

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
CREATE TABLE public.at_network_demand
(
    trading_day timestamp with time zone NOT NULL,
    network_id text NOT NULL,
    network_region text NOT NULL,
    demand_energy numeric,
    demand_market_value numeric
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
| 2014\-09\-04 00:00:00\+00:00 | NEM | SNOWY1 | None | None |
| 2022\-12\-10 00:00:00\+00:00 | NEM | SNOWY1 | None | None |
| 2009\-11\-25 00:00:00\+00:00 | NEM | SA1 | 38\.97058746666666666662 | 1149913\.7881037454916656095401000 |
| 2005\-10\-08 00:00:00\+00:00 | NEM | QLD1 | 136\.15955583333333333322 | 493805\.3323749999999996248000 |
| 2011\-01\-19 00:00:00\+00:00 | NEM | SNOWY1 | None | None |

## Table: public.at_network_flows

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
CREATE TABLE public.at_network_flows
(
    trading_interval timestamp with time zone NOT NULL,
    network_id text NOT NULL,
    network_region text NOT NULL,
    energy_imports numeric,
    energy_exports numeric,
    emissions_imports numeric,
    emissions_exports numeric,
    market_value_imports numeric,
    market_value_exports numeric
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
| 2014\-02\-23 01:45:00\+00:00 | NEM | NSW1 | 87\.53845333333334 | 0\.0 | 92\.10402319120314 | 0\.0 | 0\.0 | 0\.0 |
| 2016\-02\-04 00:50:00\+00:00 | NEM | QLD1 | 20\.794201666666666 | 0\.0 | 17\.338245505615188 | 0\.0 | 0\.0 | 0\.0 |
| 2016\-04\-25 07:25:00\+00:00 | NEM | TAS1 | 0\.0 | 0\.0 | 0\.0 | 0\.0 | 0\.0 | 0\.0 |
| 2016\-08\-10 15:55:00\+00:00 | NEM | QLD1 | 0\.0 | 81\.59685583333334 | 0\.0 | 70\.59460424150537 | 0\.0 | 0\.0 |
| 2012\-10\-16 13:25:00\+00:00 | NEM | QLD1 | 0\.0 | 72\.41796916666667 | 0\.0 | 63\.77210714461127 | 0\.0 | 0\.0 |

## Table: public.at_network_flows_v3

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
CREATE TABLE public.at_network_flows_v3
(
    trading_interval timestamp with time zone NOT NULL,
    network_id text NOT NULL,
    network_region text NOT NULL,
    energy_imports numeric,
    energy_exports numeric,
    market_value_imports numeric,
    market_value_exports numeric,
    emissions_imports numeric,
    emissions_exports numeric
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

## Table: public.balancing_summary

Total rows: 11,329,360

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
CREATE TABLE public.balancing_summary
(
    "interval" timestamp without time zone NOT NULL,
    network_id text NOT NULL,
    network_region text NOT NULL,
    forecast_load numeric,
    generation_scheduled numeric,
    generation_non_scheduled numeric,
    generation_total numeric,
    price numeric,
    is_forecast boolean,
    net_interchange numeric,
    demand_total numeric,
    price_dispatch numeric,
    net_interchange_trading numeric,
    demand numeric
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
| 2017\-11\-25 22:40:00 | NEM | VIC1 | None | None | None | None | None | False | 0\.23 | 4649\.8760 | 96\.76042 | None | 4591\.77 |
| 2020\-03\-26 08:40:00 | NEM | TAS1 | None | None | None | None | None | False | 152\.41 | 1288\.779590 | 6\.80839 | None | 1245\.23 |
| 2015\-02\-23 02:30:00 | NEM | SA1 | None | None | None | None | 19\.83 | False | \-336\.05 | 1594\.46732 | 17\.59869 | \-431\.69 | 1386\.03 |
| 2015\-02\-10 10:10:00 | NEM | QLD1 | None | None | None | None | None | False | 991\.35 | 6739\.94125 | 31\.25247 | None | 6593\.27 |
| 2024\-08\-21 00:15:00 | NEM | NSW1 | None | None | None | None | 114\.36 | False | None | None | None | None | None |

## Table: public.bom_observation

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
CREATE TABLE public.bom_observation
(
    observation_time timestamp with time zone NOT NULL,
    station_id text NOT NULL,
    temp_apparent numeric,
    temp_air numeric,
    press_qnh numeric,
    wind_dir text,
    wind_spd numeric,
    cloud text,
    cloud_type text,
    humidity numeric,
    wind_gust numeric,
    temp_max numeric,
    temp_min numeric
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
| 2021\-02\-23 22:00:00\+00:00 | 075019 | 10\.2 | 14\.5 | 1017\.3 | SSE | 17 |  |  | 54 | 20 | None | None |
| 2021\-03\-31 16:30:00\+00:00 | 066137 | 15\.6 | 15\.1 | 1024\.0 | CALM | 0 | Partly cloudy |  | 80 | 0 | None | None |
| 2021\-03\-01 08:30:00\+00:00 | 033002 | None | 25\.6 | None | CALM | 0 |  |  | None | 0 | None | None |
| 2021\-03\-22 11:08:00\+00:00 | 033119 | 28\.8 | 25\.0 | 1011\.5 | ENE | 13 | Partly cloudy |  | 98 | 22 | None | None |
| 2021\-04\-18 10:30:00\+00:00 | 074272 | 6\.6 | 7\.8 | None | CALM | 0 |  |  | 81 | 0 | None | None |

## Table: public.bom_station

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
CREATE TABLE public.bom_station
(
    code text NOT NULL,
    state text,
    name text,
    registered date,
    geom USER-DEFINED,
    feed_url text,
    is_capital boolean,
    name_alias text,
    priority integer,
    website_url text,
    altitude integer,
    web_code text
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
| 092019 | TAS | LAKE LEAKE \(ELIZABETH RIVER\) | None | 0101000020E61000009A99999999796240E17A14AE470145C0 | http://www\.bom\.gov\.au/fwo/IDT60801/IDT60801\.94979\.json | False | Lake Leake | 5 | http://www\.bom\.gov\.au/products/IDT60801/IDT60801\.94979\.shtml | 575 | None |
| 033195 | QLD | WILLIAMSON | None | 0101000020E6100000F6285C8FC2C56240B81E85EB517836C0 | http://www\.bom\.gov\.au/fwo/IDQ60801/IDQ60801\.95370\.json | False | Williamson | 5 | http://www\.bom\.gov\.au/products/IDQ60801/IDQ60801\.95370\.shtml | 27 | None |
| 250074 | QLD | NORTH TAMBORINE \(QFRJ\) | None | 0101000020E6100000AE47E17A14266340713D0AD7A3F03BC0 | http://www\.bom\.gov\.au/fwo/IDQ60801/IDQ60801\.99123\.json | False | PORTABLE QFRJ \(North Tamborine\) | 5 | http://www\.bom\.gov\.au/products/IDQ60801/IDQ60801\.99123\.shtml | 527 | None |
| 048237 | NSW | COBAR AIRPORT AWS | None | 0101000020E61000009A999999993962400AD7A3703D8A3FC0 | http://www\.bom\.gov\.au/fwo/IDN60801/IDN60801\.94710\.json | False | Cobar Airport | 5 | http://www\.bom\.gov\.au/products/IDN60801/IDN60801\.94710\.shtml | 218 | None |
| 200840 | QLD | BOUGAINVILLE REEF | None | 0101000020E6100000A4703D0AD76362407B14AE47E1FA2EC0 | http://www\.bom\.gov\.au/fwo/IDQ60801/IDQ60801\.95288\.json | False | Bougainville Reef | 5 | http://www\.bom\.gov\.au/products/IDQ60801/IDQ60801\.95288\.shtml | 0 | None |

## Table: public.crawl_history

Total rows: 791,726

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
CREATE TABLE public.crawl_history
(
    source USER-DEFINED NOT NULL,
    crawler_name text NOT NULL,
    network_id text NOT NULL,
    "interval" timestamp with time zone NOT NULL,
    inserted_records integer,
    crawled_time timestamp with time zone,
    processed_time timestamp with time zone
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
| nemweb | au\.nemweb\.current\.dispatch\_is | NEM | 2023\-11\-26 09:00:00\+00:00 | 16 | None | 2023\-11\-25 23:00:01\+00:00 |
| nemweb | au\.nemweb\.trading\_is | NEM | 2022\-08\-17 00:45:00\+00:00 | 5 | None | 2022\-08\-16 16:02:33\+00:00 |
| nemweb | au\.nemweb\.current\.dispatch\_scada | NEM | 2024\-03\-08 22:45:00\+00:00 | 455 | None | 2024\-03\-08 12:45:32\+00:00 |
| nemweb | au\.nemweb\.current\.trading\_is | NEM | 2023\-12\-09 08:50:00\+00:00 | 5 | None | 2023\-12\-14 12:49:07\+00:00 |
| nemweb | au\.nemweb\.dispatch\_scada | NEM | 2022\-07\-12 18:20:00\+00:00 | 414 | 2022\-07\-12 08:20:06\.645431\+00:00 | 2022\-07\-12 08:20:06\.645431\+00:00 |

## Table: public.crawl_meta

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
CREATE TABLE public.crawl_meta
(
    spider_name text NOT NULL,
    data jsonb,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
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
| au\.nemweb\.current\.dispatch\_is | \{'version': '2', 'last\_crawled': '2024\-09\-14T08:30:30\+10:00', 'server\_latest': '2024\-08\-03T10:50:00\+10:00', 'latest\_processed': '2024\-08\-03T10:50:00\+10:00'\} | 2023\-09\-04 10:39:36\.962104\+00:00 | 2024\-09\-13 22:30:30\.338328\+00:00 |
| au\.nemweb\.archive\.dispatch\_actual\_gen | \{'version': '2', 'last\_crawled': '2024\-09\-03T23:15:47\+10:00'\} | 2022\-07\-21 02:19:10\.279228\+00:00 | 2024\-09\-03 13:15:47\.799647\+00:00 |
| au\.nemweb\.dispatch\_scada | \{'version': '2', 'last\_crawled': '2023\-09\-26T16:59:38\+10:00', 'server\_latest': '2023\-09\-26T16:55:00\+10:00', 'latest\_processed': '2023\-09\-26T16:55:00\+10:00'\} | 2022\-06\-25 05:00:23\.039827\+00:00 | 2023\-09\-26 06:59:38\.651498\+00:00 |
| au\.nemweb\.archive\.dispatch\_is | \{'version': '2', 'last\_crawled': '2022\-10\-23T01:41:05\+11:00'\} | 2022\-07\-21 01:09:04\.417116\+00:00 | 2022\-10\-22 14:41:06\.104388\+00:00 |
| au\.nem\.current\.dispatch\_is | \{'version': '2', 'last\_crawled': '2022\-06\-27T11:21:11\+10:00', 'server\_latest': '2022\-06\-27T11:25:00\+10:00', 'latest\_processed': '2022\-06\-27T11:25:00\+10:00'\} | 2022\-06\-10 07:17:17\.371397\+00:00 | 2022\-06\-27 01:25:10\.485255\+00:00 |

## Table: public.facility

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
CREATE TABLE public.facility
(
    created_by text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    id integer NOT NULL,
    network_id text NOT NULL,
    fueltech_id text,
    status_id text,
    station_id integer,
    code text NOT NULL,
    network_code text,
    network_region text,
    network_name text,
    active boolean,
    dispatch_type USER-DEFINED NOT NULL,
    capacity_registered numeric,
    registered timestamp without time zone,
    deregistered timestamp without time zone,
    unit_id integer,
    unit_number integer,
    unit_alias text,
    unit_capacity numeric,
    approved boolean,
    approved_by text,
    approved_at timestamp with time zone,
    emissions_factor_co2 numeric,
    interconnector boolean,
    interconnector_region_to text,
    data_first_seen timestamp with time zone,
    data_last_seen timestamp with time zone,
    expected_closure_date timestamp without time zone,
    expected_closure_year integer,
    interconnector_region_from text,
    emission_factor_source text,
    include_in_geojson boolean
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
| opennem\.registry | 2020\-12\-09 15:34:03\.178535\+00:00 | 2024\-06\-07 13:11:59\.838421\+00:00 | 336 | NEM | coal\_brown | retired | 242 | PLAYFB3 | NEM | SA1 | None | True | GENERATOR | 60\.0 | None | None | None | None | None | None | True | None | 2020\-12\-09 15:34:03\.178523\+00:00 | 1\.5090411 | False | None | 1998\-12\-06 15:50:00\+00:00 | 1999\-05\-24 19:40:00\+00:00 | None | None | None | None | True |
| opennem\.importer\.trading\_flows | 2021\-03\-06 09:41:38\.312087\+00:00 | 2021\-03\-06 20:41:38\.572730\+00:00 | 626 | NEM | exports | operating | 449 | NEM\_FLOW\_TAS1\_EXPORTS | None | TAS1 | None | True | GENERATOR | None | None | None | None | None | None | None | True | opennem\.importer\.trading\_flows | None | None | False | None | 2009\-06\-30 14:25:00\+00:00 | 2021\-04\-30 13:55:00\+00:00 | None | None | None | None | True |
| opennem\.importer\.rooftop | 2021\-04\-12 07:06:35\.843691\+00:00 | 2023\-02\-22 09:55:06\.681664\+00:00 | 640 | AEMO\_ROOFTOP\_BACKFILL | solar\_rooftop | operating | 473 | ROOFTOP\_AEMO\_ROOFTOP\_BACKFILL\_NSW | None | NSW1 | None | False | GENERATOR | None | None | None | None | None | None | None | False | opennem\.importer\.rooftop | None | None | False | None | None | None | None | None | None | None | True |
| opennem\.registry | 2020\-12\-09 15:34:46\.045373\+00:00 | 2023\-03\-31 04:51:20\.650943\+00:00 | 497 | NEM | solar\_utility | operating | 355 | YARANSF1 | NEM | QLD1 | None | True | GENERATOR | 121\.0 | None | None | None | None | None | None | True | None | 2020\-12\-09 15:34:46\.045353\+00:00 | 0\.0 | False | None | 2020\-01\-06 22:05:00\+00:00 | 2024\-08\-03 00:50:00\+00:00 | None | None | None | None | True |
| opennem\.registry | 2020\-12\-09 15:33:14\.423692\+00:00 | 2023\-03\-31 04:51:34\.222163\+00:00 | 46 | NEM | hydro | operating | 35 | BAPS | NEM | VIC1 | None | True | GENERATOR | 12\.0 | None | None | None | None | None | None | True | None | 2020\-12\-09 15:33:14\.423672\+00:00 | 0\.0 | False | None | None | None | None | None | None | None | True |

## Table: public.facility_scada

Total rows: 769,757,256

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
CREATE TABLE public.facility_scada
(
    network_id text NOT NULL,
    "interval" timestamp without time zone NOT NULL,
    facility_code text NOT NULL,
    generated numeric,
    eoi_quantity numeric,
    is_forecast boolean NOT NULL,
    energy_quality_flag numeric NOT NULL,
    energy numeric
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
| NEM | 2019\-04\-06 09:20:00 | TORRB1 | 0\.0 | None | False | 1 | 0E\-20 |
| NEM | 2015\-12\-17 11:35:00 | YWPS2 | 300\.49875 | None | False | 1 | 25\.0728912500000000 |
| NEM | 2022\-09\-29 10:10:00 | GORDON | 0\.0 | None | False | 0 | 0E\-20 |
| NEM | 2005\-10\-13 23:15:00 | CALL\_A\_3 | 0\.0 | None | False | 1 | 0E\-20 |
| NEM | 2021\-06\-27 22:35:00 | APD01 | 0\.0 | None | False | 0 | 0E\-20 |

## Table: public.facility_status

Total rows: 12

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| code | text | N/A | No |
| label | text | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE public.facility_status
(
    code text NOT NULL,
    label text
);

```

### Constraints

- PRIMARY KEY (code)

### Indexes

- CREATE UNIQUE INDEX facility_status_pkey ON public.facility_status USING btree (code)

### Sample Data

| code | label |
| --- | --- |
| cancelled | Cancelled |
| operating | Operating |
| permitted | Permitted |
| mothballed | Mothballed |
| commissioning | Commissioning |

## Table: public.feedback

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
CREATE TABLE public.feedback
(
    id integer NOT NULL,
    subject text NOT NULL,
    description text,
    email text,
    twitter text,
    user_ip text,
    user_agent text,
    created_at timestamp with time zone,
    alert_sent boolean NOT NULL
);

```

### Constraints

- PRIMARY KEY (id)

### Indexes

- CREATE UNIQUE INDEX feedback_pkey ON public.feedback USING btree (id)

## Table: public.fueltech

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
CREATE TABLE public.fueltech
(
    created_by text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    code text NOT NULL,
    label text,
    renewable boolean,
    fueltech_group_id text
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
| None | 2020\-12\-09 01:46:30\.253904\+00:00 | None | exports | Network Export | False | None |
| None | 2024\-08\-10 04:20:45\.089031\+00:00 | None | battery | Battery | True | None |
| None | 2020\-12\-09 01:46:29\.145850\+00:00 | 2022\-10\-04 06:24:38\.667053\+00:00 | bioenergy\_biomass | Biomass | False | bioenergy |
| None | 2020\-12\-09 01:46:29\.731852\+00:00 | 2022\-10\-04 06:24:39\.180047\+00:00 | pumps | Pumps | True | pumps |
| None | 2020\-12\-09 01:46:29\.376830\+00:00 | 2022\-10\-04 06:24:38\.865319\+00:00 | gas\_ccgt | Gas \(CCGT\) | False | gas |

## Table: public.fueltech_group

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
CREATE TABLE public.fueltech_group
(
    created_by text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    code text NOT NULL,
    label text,
    color text,
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
| None | 2022\-10\-04 06:24:38\.163568\+00:00 | 2024\-08\-13 02:51:57\.473752\+00:00 | solar | Solar | \#FED500 | True |
| None | 2022\-10\-04 06:24:38\.411012\+00:00 | None | bioenergy | Bioenergy | \#A3886F | False |
| None | 2022\-10\-04 06:24:38\.114476\+00:00 | 2024\-08\-13 02:51:57\.357664\+00:00 | wind | Wind | \#417505 | True |
| None | 2022\-10\-04 06:24:38\.363459\+00:00 | None | distillate | Distillate | \#F35020 | False |
| None | 2022\-10\-04 06:24:38\.263261\+00:00 | 2024\-08\-13 02:51:57\.662572\+00:00 | battery\_discharging | Battery \(Discharging\) | \#00A2FA | True |

## Table: public.location

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
CREATE TABLE public.location
(
    id integer NOT NULL,
    address1 text,
    address2 text,
    locality text,
    state text,
    postcode text,
    place_id text,
    geocode_approved boolean,
    geocode_skip boolean,
    geocode_processed_at timestamp without time zone,
    geocode_by text,
    geom USER-DEFINED,
    osm_way_id text,
    boundary USER-DEFINED
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
| 13506 |  |  |  | QLD | None | None | True | False | None | opennem\.registry | 0101000020E6100000CCF33BA85FEE6240941BA08F8DB73AC0 | None | None |
| 13519 |  |  |  | QLD | None | None | True | False | None | opennem\.registry | 0101000020E6100000715DA10BA7DC6240F17C15F7E91D3BC0 | None | None |
| 13691 |  |  |  | SA | None | None | True | False | None | opennem\.registry | 0101000020E6100000C7B7D40D50456140A823534C86D840C0 | None | None |
| 13797 | None | None | Moorabool | VIC | 3213 | None | False | False | None | None | 0101000020E61000009824E9E54F0962401D72BB57E60443C0 | None | None |
| 3 | None | None | None | VIC | None | None | False | False | None | None | None | None | None |

## Table: public.milestones

Total rows: 18,789

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
CREATE TABLE public.milestones
(
    instance_id uuid NOT NULL,
    record_id text NOT NULL,
    "interval" timestamp without time zone NOT NULL,
    significance integer NOT NULL,
    value double precision NOT NULL,
    network_id text,
    fueltech_id text,
    description character varying,
    period character varying,
    aggregate character varying NOT NULL,
    metric character varying,
    value_unit character varying,
    description_long character varying,
    network_region text,
    previous_instance_id uuid
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
| cc2eb7f7\-f3be\-4c3c\-a928\-4a2f6ef5d1ec | au\.nem\.vic1\.wind\.energy\.week\.high | 2023\-06\-05 00:00:00 | 7 | 365319\.6225 | NEM | wind | Weekly wind energy high record for NEM in Victoria | week | high | energy | MWh | None | VIC1 | 684d9135\-1840\-433c\-8a11\-b98241252a6c |
| 98b21d75\-9d79\-48a7\-9ad7\-6d582dd96236 | au\.nem\.tas1\.distillate\.power\.interval\.low | 2016\-03\-11 17:10:00 | 1 | \-0\.19 | NEM | distillate | Interval distillate power low record for NEM in Tasmania | interval | low | power | MW | None | TAS1 | a9126a81\-a524\-49b5\-83ea\-2c1cd46d438d |
| b9da5ace\-2482\-4a24\-8ddf\-9e7c1baef6db | au\.nem\.solar\.energy\.day\.high | 2019\-11\-27 00:00:00 | 9 | 47449\.123 | NEM | solar | Daily solar energy high record for NEM | day | high | energy | MWh | None | None | 1ce5bd84\-2f1e\-4e62\-8cd1\-7e139debca5f |
| 5499c12e\-cd8c\-49fa\-b2b6\-7340ff1a0c93 | au\.nem\.vic1\.gas\.energy\.week\.high | 2017\-07\-03 00:00:00 | 6 | 137976\.0744 | NEM | gas | Weekly gas energy high record for NEM in Victoria | week | high | energy | MWh | None | VIC1 | 5a2ce619\-5dbf\-4299\-b80c\-edb98ca91bdb |
| 58527ebb\-8c73\-4da8\-9613\-33ac55b01a0d | au\.nem\.vic1\.coal\.power\.interval\.high | 2002\-06\-27 01:55:00 | 4 | 6425\.02 | NEM | coal | Interval coal power high record for NEM in Victoria | interval | high | power | MW | None | VIC1 | 5eacab51\-b655\-4ff8\-b1ce\-bfe7508537fe |

## Table: public.network

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
CREATE TABLE public.network
(
    created_by text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    code text NOT NULL,
    country text NOT NULL,
    label text,
    timezone text NOT NULL,
    interval_size integer NOT NULL,
    "offset" integer,
    timezone_database text,
    export_set boolean NOT NULL,
    interval_shift integer NOT NULL,
    network_price text NOT NULL,
    data_start_date timestamp with time zone,
    data_end_date timestamp with time zone
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
| None | 2020\-12\-09 01:46:31\.057929\+00:00 | 2024\-08\-10 04:32:14\.138129\+00:00 | NEM | au | NEM | Australia/Brisbane | 5 | 600 | AEST | True | 5 | NEM | 1998\-12\-06 15:40:00\+00:00 | 2024\-08\-03 00:15:00\+00:00 |
| None | 2020\-12\-09 01:46:31\.176786\+00:00 | 2024\-08\-03 00:15:22\.319623\+00:00 | APVI | au | APVI | Australia/Perth | 15 | 600 | AWST | False | 0 | WEM | 2015\-03\-19 20:15:00\+00:00 | 2024\-08\-03 00:00:00\+00:00 |
| None | 2023\-02\-22 09:54:49\.679305\+00:00 | 2024\-08\-10 04:32:14\.781558\+00:00 | OPENNEM\_ROOFTOP\_BACKFILL | au | OpenNEM Rooftop Backfill | Australia/Brisbane | 30 | 600 | AEST | False | 0 | NEM | 2015\-03\-19 20:15:00\+00:00 | 2018\-02\-28 09:30:00\+00:00 |
| None | 2020\-12\-09 01:46:31\.118850\+00:00 | 2024\-08\-02 04:15:22\.375279\+00:00 | WEM | au | WEM | Australia/Perth | 30 | 480 | AWST | True | 0 | WEM | 2006\-09\-19 16:00:00\+00:00 | 2024\-08\-01 23:55:00\+00:00 |
| None | 2021\-04\-12 07:06:18\.835747\+00:00 | 2024\-08\-10 04:32:14\.674557\+00:00 | AEMO\_ROOFTOP\_BACKFILL | au | AEMO Rooftop Backfill | Australia/Brisbane | 30 | 600 | AEST | False | 0 | NEM | None | None |

## Table: public.network_region

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
CREATE TABLE public.network_region
(
    created_by text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    network_id text NOT NULL,
    code text NOT NULL,
    timezone text,
    timezone_database text,
    "offset" integer,
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
| None | 2021\-04\-09 10:15:56\.445329\+00:00 | None | AEMO\_ROOFTOP | TAS1 | None | None | None | True |
| None | 2020\-12\-09 01:46:31\.363840\+00:00 | None | NEM | QLD1 | None | None | None | True |
| None | 2021\-04\-09 10:15:56\.449008\+00:00 | None | AEMO\_ROOFTOP | SA1 | None | None | None | True |
| None | 2020\-12\-09 01:46:31\.302424\+00:00 | None | NEM | NSW1 | None | None | None | True |
| None | 2020\-12\-09 01:46:31\.480819\+00:00 | None | NEM | TAS1 | None | None | None | True |

## Table: public.participant

Total rows: 201

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| id | integer | N/A | No |
| code | text | N/A | Yes |
| name | text | N/A | Yes |
| network_name | text | N/A | Yes |
| network_code | text | N/A | Yes |
| country | text | N/A | Yes |
| abn | text | N/A | Yes |
| approved | boolean | N/A | Yes |
| approved_by | text | N/A | Yes |
| approved_at | timestamp with time zone | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE public.participant
(
    id integer NOT NULL,
    code text,
    name text,
    network_name text,
    network_code text,
    country text,
    abn text,
    approved boolean,
    approved_by text,
    approved_at timestamp with time zone
);

```

### Constraints

- PRIMARY KEY (id)

### Indexes

- CREATE UNIQUE INDEX participant_pkey ON public.participant USING btree (id)
- CREATE UNIQUE INDEX ix_participant_code ON public.participant USING btree (code)

### Sample Data

| id | code | name | network\_name | network\_code | country | abn | approved | approved\_by | approved\_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 130 | Grenough | SRVGRSF | None | None | None | None | False | None | None |
| 200 | Wpso | WesternPower | None | None | None | None | False | None | None |
| 12 | GRIFFINP | BluewatersPower1Pty | Bluewaters Power 1 Pty Ltd | None | None | None | False | None | 2021\-01\-15 04:20:48\.407158\+00:00 |
| 32 | WGRES | WasteGasResourcesPty | Waste Gas Resources Pty Ltd | None | None | None | False | None | 2021\-01\-15 04:20:49\.007619\+00:00 |
| 196 | Wgres | WasteGasResources | None | None | None | None | False | None | None |

## Table: public.station

Total rows: 551

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| created_by | text | N/A | Yes |
| created_at | timestamp with time zone | N/A | Yes |
| updated_at | timestamp with time zone | N/A | Yes |
| id | integer | N/A | No |
| participant_id | integer | N/A | Yes |
| location_id | integer | N/A | Yes |
| code | text | N/A | No |
| name | text | N/A | Yes |
| description | text | N/A | Yes |
| wikipedia_link | text | N/A | Yes |
| wikidata_id | text | N/A | Yes |
| network_code | text | N/A | Yes |
| network_name | text | N/A | Yes |
| approved | boolean | N/A | Yes |
| approved_by | text | N/A | Yes |
| approved_at | timestamp with time zone | N/A | Yes |
| website_url | text | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE public.station
(
    created_by text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    id integer NOT NULL,
    participant_id integer,
    location_id integer,
    code text NOT NULL,
    name text,
    description text,
    wikipedia_link text,
    wikidata_id text,
    network_code text,
    network_name text,
    approved boolean,
    approved_by text,
    approved_at timestamp with time zone,
    website_url text
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

| created\_by | created\_at | updated\_at | id | participant\_id | location\_id | code | name | description | wikipedia\_link | wikidata\_id | network\_code | network\_name | approved | approved\_by | approved\_at | website\_url |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| opennem\.registry | 2020\-12\-09 15:32:39\.826093\+00:00 | 2024\-06\-07 13:12:32\.607997\+00:00 | 385 | None | 13398 | HENDERSON\_RENEWABLE | Henderson | None | None | None | None | Henderson | True | opennem\.importer\.facilities | 2024\-06\-07 23:12:32\.653545\+00:00 | None |
| opennem\.registry | 2020\-12\-09 15:32:39\.826093\+00:00 | 2024\-06\-07 13:12:04\.924319\+00:00 | 40 | None | 13455 | BASTYAN | Bastyan | The Bastyan Power Station is a conventional hydroelectric power station located in Western Tasmania, Australia\. | https://en\.wikipedia\.org/wiki/Bastyan\_Power\_Station | Q4868381 | None | Bastyan | True | opennem\.importer\.facilities | 2024\-06\-07 23:12:04\.973827\+00:00 | None |
| opennem\.registry | 2020\-12\-09 15:32:39\.826093\+00:00 | 2024\-06\-07 13:11:58\.932743\+00:00 | 228 | None | 13643 | NPPPPS | Pelican Point | The Pelican Point Power Station is located at Pelican Point, 20 km from the centre of Adelaide, South Australia on the Lefevre Peninsula\. It is operated by Engie \(previously known as GDF Suez Australi\.\.\. | https://en\.wikipedia\.org/wiki/Pelican\_Point\_Power\_Station | Q7161425 | None | Pelican Point | True | opennem\.importer\.facilities | 2024\-06\-07 23:11:58\.982684\+00:00 | None |
| opennem\.registry | 2020\-12\-09 15:32:39\.826093\+00:00 | 2024\-06\-07 13:12:01\.558433\+00:00 | 276 | None | 13691 | SNOWTOWN | Snowtown | The Snowtown wind farms are located on the Barunga and Hummocks ranges west of Snowtown in the Mid North of South Australia, around 150 kilometres \(93 mi\) north of the state capital, Adelaide\. They we\.\.\. | https://en\.wikipedia\.org/wiki/Snowtown\_Wind\_Farm | Q7548732 | None | Snowtown | True | opennem\.importer\.facilities | 2024\-06\-07 23:12:01\.604118\+00:00 | None |
| opennem\.registry | 2020\-12\-09 15:32:39\.826093\+00:00 | 2024\-06\-07 13:11:44\.346576\+00:00 | 200 | None | 13615 | MBAHNTH | Moranbah North | None | None | None | None | Moranbah North | True | opennem\.importer\.facilities | 2024\-06\-07 23:11:44\.398877\+00:00 | None |

## Table: public.stats

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
CREATE TABLE public.stats
(
    created_by text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    stat_date timestamp with time zone NOT NULL,
    country text NOT NULL,
    stat_type text NOT NULL,
    value numeric
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
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 2002\-06\-30 00:00:00\+00:00 | au | CPI | 76\.6 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 1930\-12\-01 00:00:00\+00:00 | au | CPI | 2\.6 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 1943\-06\-01 00:00:00\+00:00 | au | CPI | 3\.2 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 1970\-06\-01 00:00:00\+00:00 | au | CPI | 9\.7 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 2013\-03\-31 00:00:00\+00:00 | au | CPI | 102\.4 |

## Table: public.task_profile

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
CREATE TABLE public.task_profile
(
    id uuid NOT NULL,
    task_name text NOT NULL,
    time_start timestamp with time zone NOT NULL,
    time_end timestamp with time zone,
    time_sql timestamp with time zone,
    time_cpu timestamp with time zone,
    errors integer NOT NULL,
    retention_period text,
    level text,
    invokee_name text
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
| 68134e66\-f2c0\-41b6\-b31f\-88a544b00066 | nem\_dispatch\_scada\_crawl | 2024\-03\-09 20:00:32\.442209\+00:00 | 2024\-03\-09 20:03:55\.623407\+00:00 | None | None | 0 | forever | noisy |  |
| ed38d054\-6374\-4906\-a74f\-dbb0a3f8ee06 | run\_aggregate\_flow\_for\_interval\_v3 | 2024\-04\-05 11:20:02\.500212\+00:00 | 2024\-04\-05 11:20:02\.670654\+00:00 | None | None | 0 | forever | info |  |
| 96f1c79b\-ea0c\-402f\-bd96\-ffc548de8245 | run\_network\_data\_range\_update | 2024\-03\-06 23:15:34\.708563\+00:00 | 2024\-03\-06 23:15:34\.897715\+00:00 | None | None | 0 | forever | noisy |  |
| 9ea13397\-6e52\-4891\-a589\-45beafc0b566 | wem\_per\_interval\_check | 2024\-07\-23 19:38:26\.149520\+00:00 | 2024\-07\-23 19:38:39\.497578\+00:00 | None | None | 0 | forever | noisy |  |
| f1518578\-3872\-4943\-af5f\-541679c11c76 | nem\_dispatch\_scada\_crawl | 2024\-04\-21 00:20:43\.435964\+00:00 | 2024\-04\-21 00:23:42\.918426\+00:00 | None | None | 0 | forever | noisy |  |
