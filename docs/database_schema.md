# Database Schema

Database: opennem
PostgreSQL version: PostgreSQL 16.4 (Ubuntu 16.4-1.pgdg22.04+1) on x86_64-pc-linux-gnu, compiled by gcc (Ubuntu 11.4.0-1ubuntu1~22.04) 11.4.0, 64-bit
Schemas: public

## Table of Contents

| Schema | Table Name | Row Count |
|--------|------------|----------|
| public | [aemo_facility_data](#public-aemo-facility-data) | 0 |
| public | [aemo_market_notices](#public-aemo-market-notices) | 824 |
| public | [alembic_version](#public-alembic-version) | 1 |
| public | [api_keys](#public-api-keys) | 1 |
| public | [at_facility_daily](#public-at-facility-daily) | 2,885,368 |
| public | [at_network_demand](#public-at-network-demand) | 62,753 |
| public | [at_network_flows](#public-at-network-flows) | 7,917,760 |
| public | [at_network_flows_v3](#public-at-network-flows-v3) | 0 |
| public | [balancing_summary](#public-balancing-summary) | 11,327,830 |
| public | [bom_observation](#public-bom-observation) | 5,920,234 |
| public | [bom_station](#public-bom-station) | 773 |
| public | [crawl_history](#public-crawl-history) | 790,804 |
| public | [crawl_meta](#public-crawl-meta) | 50 |
| public | [facility](#public-facility) | 787 |
| public | [facility_scada](#public-facility-scada) | 769,611,359 |
| public | [facility_status](#public-facility-status) | 12 |
| public | [feedback](#public-feedback) | 94 |
| public | [fueltech](#public-fueltech) | 26 |
| public | [fueltech_group](#public-fueltech-group) | 10 |
| public | [location](#public-location) | 551 |
| public | [milestones](#public-milestones) | 14,372 |
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

## Table: public.aemo_market_notices

Total rows: 824

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
| 118001 | RECLASSIFY CONTINGENCY | 2024\-08\-31 03:54:41 | 2024\-08\-31 00:00:00 | Reclassification of a Non\-Credible Contingency Event: Palmerston \- Hadspen 3 & 4 110kV line and  line in TAS1 due to Lightning\. | Reclassification of a Non\-Credible Contingency Event as a Credible Contingency Event due to Lightning\. AEMO considers the simultaneous trip of the following circuits to now be more likely and reasonab\.\.\. |
| 117663 | MARKET INTERVENTION | 2024\-08\-13 14:11:27 | 2024\-08\-13 00:00:00 | Cancellation: Direction issued to:  AGL SA Generation Pty Limited \- TORRB2 TORRENS ISLAN | AEMO ELECTRICITY MARKET NOTICE

Cancellation: Direction issued to:  AGL SA Generation Pty Limited \- TORRB2 TORRENS ISLAN

Refer to Market Notice 117656

Direction is cancelled from: 1400 hrs 13/08/202\.\.\. |
| 117687 | NON\-CONFORMANCE | 2024\-08\-15 18:15:18 | 2024\-08\-15 18:15:00 | NON\-CONFORMANCE Region QLD1 Thursday, 15 August 2024 | AEMO ELECTRICITY MARKET NOTICE

NON\-CONFORMANCE QLD1 Region Thursday, 15 August 2024

AEMO has declared the following unit as non\-conforming under clause 3\.8\.23 of the National Electricity Rules:

Uni\.\.\. |
| 118075 | MARKET INTERVENTION | 2024\-09\-02 17:02:42 | 2024\-09\-02 00:00:00 | Direction \- SA region 02/09/2024 | AEMO ELECTRICITY MARKET NOTICE

Direction \- SA region 02/09/2024

In accordance with section 116 of the National Electricity Law, AEMO has issued a direction to a participant in the SA region\. For the\.\.\. |
| 117813 | MARKET INTERVENTION | 2024\-08\-26 13:09:15 | 2024\-08\-26 00:00:00 | Direction \- SA region 26/08/2024 | AEMO ELECTRICITY MARKET NOTICE

Direction \- SA region 26/08/2024

In accordance with section 116 of the National Electricity Law, AEMO has issued a direction to a participant in the SA region\. For the\.\.\. |

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
| 2014\-11\-16 00:00:00\+00:00 | NEM | YAMBUKWF | wind | 480\.5958344166666536 | 8635\.133887234865176813312 | 0E\-17 | VIC1 |
| 2010\-08\-15 00:00:00\+00:00 | NEM | JLA03 | gas\_ocgt | 0 | 0 | 0 | VIC1 |
| 2010\-01\-26 00:00:00\+00:00 | NEM | MEADOWBK | hydro | 307\.4862658333333445 | 8922\.00361428525864608205 | 0E\-17 | TAS1 |
| 2016\-02\-07 00:00:00\+00:00 | NEM | YABULU2 | gas\_ccgt | 0 | 0 | 0 | QLD1 |
| 2012\-05\-13 00:00:00\+00:00 | NEM | MEADOWBK | hydro | 499\.0734866666666711 | 21660\.837533083500083903692 | 0E\-17 | TAS1 |

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
| 2004\-09\-22 00:00:00\+00:00 | NEM | SA1 | 5\.65844333333333333333 | 152696\.0092666666666666399000 |
| 2015\-04\-04 00:00:00\+00:00 | WEM | WEM | None | None |
| 2014\-12\-12 00:00:00\+00:00 | NEM | SNOWY1 | None | None |
| 2021\-07\-06 00:00:00\+00:00 | NEM | TAS1 | 34\.60900663416666666663 | 2161023\.4390509746250256616890000 |
| 2023\-05\-29 00:00:00\+00:00 | NEM | QLD1 | 151\.10887239666666666669 | 18460632\.9024907426166655529663000 |

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
    energy_imports numeric NULL,
    energy_exports numeric NULL,
    emissions_imports numeric NULL,
    emissions_exports numeric NULL,
    market_value_imports numeric NULL,
    market_value_exports numeric NULL,
    "........pg.dropped.10........" - NULL,
    "........pg.dropped.11........" - NULL,
    "........pg.dropped.12........" - NULL
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
| 2020\-07\-19 05:50:00\+00:00 | NEM | NSW1 | 95\.86797833333333 | 0\.0 | 71\.77886448202116 | 0\.0 | 0\.0 | 0\.0 |
| 2023\-11\-01 06:05:00\+00:00 | NEM | VIC1 | 37\.33038833333333 | 10\.696168333333333 | 4\.238212829917947 | 9\.621576478835465 | 0\.0 | 0\.0 |
| 2018\-08\-03 07:55:00\+00:00 | NEM | SA1 | 0\.0 | 2\.2041441666666666 | 0\.0 | 0\.5115317815000612 | 0\.0 | 0\.0 |
| 2023\-09\-17 23:00:00\+00:00 | NEM | TAS1 | 13\.016666666666667 | 0\.0 | 10\.531295910567536 | 0\.0 | 0\.0 | 0\.0 |
| 2017\-12\-31 08:30:00\+00:00 | NEM | QLD1 | 9\.39974 | 0\.0 | 7\.962718572652248 | 0\.0 | 0\.0 | 0\.0 |

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

## Table: public.balancing_summary

Total rows: 11,327,830

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
| 2022\-11\-20 05:05:00 | NEM | TAS1 | None | None | None | None | 11\.16 | False | \-177\.5 | 1122\.177530 | 11\.16 | None | 981\.21 |
| 2009\-10\-12 00:25:00 | NEM | VIC1 | None | None | None | None | None | False | 884\.11 | 5143\.3315 | 10\.89 | None | 5030\.18 |
| 2023\-05\-11 14:00:00 | NEM | NSW1 | None | None | None | None | 88\.88 | False | \-1252\.13 | 6911\.600710 | 88\.88 | None | 6523\.53 |
| 2014\-10\-04 04:35:00 | NEM | SA1 | None | None | None | None | None | False | \-6\.55 | 1118\.76009 | 20\.53205 | None | 925\.3 |
| 2023\-08\-02 14:00:00 | WEM | WEM | None | None | None | 2478\.732 | 155\.25 | False | None | None | None | None | None |

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
| 2020\-12\-14 21:50:00\+00:00 | 250061 | 30\.9 | 28\.7 | None | N | 11 |  |  | 63 | 13 | None | None |
| 2021\-04\-04 05:40:00\+00:00 | 250099 | 24\.5 | 25\.1 | None | NNE | 6 |  |  | 42 | 9 | None | None |
| 2023\-04\-18 23:30:00\+00:00 | 086338 | 13\.1 | 15\.2 | 1022\.1 | WSW | 9\.0 | None | None | 64\.0 | 20\.0 | None | None |
| 2021\-02\-18 19:30:00\+00:00 | 055325 | 16\.3 | 15\.2 | 1019\.2 | SSW | 2 |  |  | 97 | 7 | None | None |
| 2020\-12\-07 19:00:00\+00:00 | 088164 | \-0\.2 | 5\.5 | None | WSW | 24 |  |  | 97 | 33 | None | None |

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
| 109504 | WA | ESPERANCE NTC AWS | None | 0101000020E61000009A99999999795E408FC2F5285CEF40C0 | http://www\.bom\.gov\.au/fwo/IDW60801/IDW60801\.95648\.json | False | Esperance Harbour | 5 | http://www\.bom\.gov\.au/products/IDW60801/IDW60801\.95648\.shtml | 0 | None |
| 091344 | TAS | BURNIE NTC AWS | None | 0101000020E610000085EB51B81E3D624066666666668644C0 | http://www\.bom\.gov\.au/fwo/IDT60801/IDT60801\.95963\.json | False | Burnie Port | 5 | http://www\.bom\.gov\.au/products/IDT60801/IDT60801\.95963\.shtml | 0 | None |
| 097083 | TAS | SCOTTS PEAK DAM | None | 0101000020E6100000713D0AD7A348624085EB51B81E8545C0 | http://www\.bom\.gov\.au/fwo/IDT60801/IDT60801\.95958\.json | False | Scotts Peak | 5 | http://www\.bom\.gov\.au/products/IDT60801/IDT60801\.95958\.shtml | 408 | None |
| 250107 | TAS | TAS PARKS WILDLIFE PORTABLE D | None | 0101000020E610000066666666663E624033333333339345C0 | http://www\.bom\.gov\.au/fwo/IDT60801/IDT60801\.99148\.json | False | Davey Gorge \(PWS\) | 5 | http://www\.bom\.gov\.au/products/IDT60801/IDT60801\.99148\.shtml | 50 | None |
| 200831 | QLD | GANNET CAY | None | 0101000020E6100000D7A3703D0A0F63407B14AE47E1FA35C0 | http://www\.bom\.gov\.au/fwo/IDQ60801/IDQ60801\.94379\.json | False | Gannett Cay | 5 | http://www\.bom\.gov\.au/products/IDQ60801/IDQ60801\.94379\.shtml | 2 | None |

## Table: public.crawl_history

Total rows: 790,804

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
    source crawlersource NOT NULL,
    crawler_name text NOT NULL,
    network_id text NOT NULL,
    "interval" timestamp with time zone NOT NULL,
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
| nemweb | au\.nemweb\.dispatch\_is | NEM | 2023\-06\-25 01:55:00\+00:00 | 16 | None | 2023\-06\-24 15:55:01\+00:00 |
| nemweb | au\.nemweb\.dispatch\_is | NEM | 2023\-06\-08 00:05:00\+00:00 | 16 | None | 2023\-06\-07 14:05:02\+00:00 |
| nemweb | au\.nemweb\.dispatch\_scada | NEM | 2022\-09\-10 09:10:00\+00:00 | 414 | None | 2022\-09\-09 23:10:55\+00:00 |
| nemweb | au\.nemweb\.current\.dispatch\_scada | NEM | 2024\-06\-26 23:30:00\+00:00 | 460 | None | 2024\-06\-26 13:30:13\+00:00 |
| nemweb | au\.nemweb\.trading\_is | NEM | 2023\-07\-23 23:15:00\+00:00 | 5 | None | 2023\-07\-23 13:15:02\+00:00 |

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
| au\.mms\.meterdata\_gen\_duid | \{'version': '2', 'last\_crawled': '2023\-04\-01T15:21:32\+11:00'\} | 2023\-03\-30 12:12:55\.510477\+00:00 | 2023\-04\-01 04:21:32\.569705\+00:00 |
| au\.wem\.live\.balancing | \{'version': '2', 'last\_crawled': '2024\-01\-15T07:33:53\+11:00', 'server\_latest': '2024\-01\-15T05:30:00\+08:00', 'latest\_processed': '2024\-01\-15T05:30:00\+08:00'\} | 2022\-06\-10 05:54:04\.974218\+00:00 | 2024\-01\-14 20:33:53\.360964\+00:00 |
| au\.nem\.dispatch | \{'version': '2', 'last\_crawled': '2022\-07\-27T11:41:10\+10:00', 'server\_latest': '2022\-07\-20T04:00:00\+10:00', 'latest\_processed': '2022\-07\-20T04:00:00\+10:00'\} | 2022\-06\-10 10:08:08\.977778\+00:00 | 2022\-07\-27 01:41:10\.856443\+00:00 |
| au\.nemweb\.archive\.dispatch\_is | \{'version': '2', 'last\_crawled': '2022\-10\-23T01:41:05\+11:00'\} | 2022\-07\-21 01:09:04\.417116\+00:00 | 2022\-10\-22 14:41:06\.104388\+00:00 |

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
| opennem\.registry | 2020\-12\-09 15:33:58\.768421\+00:00 | 2023\-03\-31 04:51:41\.352321\+00:00 | 306 | NEM | hydro | operating | 219 | MURRAY | NEM | VIC1 | None | True | GENERATOR | 1500\.0 | None | None | None | None | None | None | True | None | 2020\-12\-09 15:33:58\.768413\+00:00 | 0\.0 | False | None | 2001\-07\-14 14:40:00\+00:00 | 2024\-08\-03 00:50:00\+00:00 | None | None | None | None | True |
| opennem\.init | 2023\-04\-26 23:10:23\.204804\+00:00 | None | 781 | NEM | solar\_utility | operating | 546 | AVLSF1 | None | NSW1 | None | True | GENERATOR | 245\.0 | None | None | None | None | None | None | False | None | None | 0\.0 | False | None | 2023\-03\-28 03:25:00\+00:00 | 2024\-08\-03 00:50:00\+00:00 | None | None | None | None | True |
| opennem\.registry | 2020\-12\-09 15:33:35\.892870\+00:00 | 2024\-06\-07 13:11:19\.484806\+00:00 | 158 | NEM | coal\_black | operating | 118 | ER03 | NEM | NSW1 | None | True | GENERATOR | 720\.0 | None | None | None | None | None | None | True | None | 2020\-12\-09 15:33:35\.892859\+00:00 | 0\.91014305 | False | None | 1998\-12\-06 15:50:00\+00:00 | 2024\-08\-03 00:50:00\+00:00 | None | None | None | None | True |
| opennem\.init | 2022\-06\-16 07:54:45\.510705\+00:00 | 2024\-06\-06 05:16:35\.293826\+00:00 | 732 | NEM | solar\_utility | committed | 519 | BLUEGSF1 | None | QLD1 | None | True | GENERATOR | 183\.0 | None | None | None | None | None | None | True | None | None | 0\.0 | False | None | 2022\-08\-01 03:15:00\+00:00 | 2024\-08\-03 00:50:00\+00:00 | None | None | None | None | True |
| opennem\.registry | 2020\-12\-09 15:34:57\.517102\+00:00 | 2024\-06\-07 13:12:35\.771021\+00:00 | 575 | WEM | gas\_ocgt | operating | 409 | PINJAR\_GT7 | WEM | WEM | None | True | GENERATOR | 39\.3 | 2003\-07\-01 00:00:00 | None | None | None | None | None | True | None | 2020\-12\-09 15:34:57\.517090\+00:00 | 0\.82 | False | None | 2013\-12\-21 06:30:00\+00:00 | 2024\-07\-22 03:45:00\+00:00 | None | None | None | None | True |

## Table: public.facility_scada

Total rows: 769,611,359

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
| NEM | 2001\-01\-29 14:50:00 | SNOWY6 | 58\.0 | None | False | 1 | 4\.8333333333333333 |
| NEM | 2014\-05\-27 18:45:00 | LD03 | 0\.0 | None | False | 1 | 0E\-20 |
| NEM | 2010\-05\-01 02:35:00 | SWAN\_B\_2 | 47\.52 | None | False | 1 | 4\.0020000000000000 |
| NEM | 2023\-06\-28 10:30:00 | GULLRSF1 | 0\.80499 | None | False | 0 | 0\.07124916666666666667 |
| NEM | 2012\-08\-19 23:00:00 | WKIEWA1 | 10\.93 | None | False | 1 | 0\.90875000000000000000 |

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
    "........pg.dropped.1........" - NULL,
    "........pg.dropped.2........" - NULL,
    "........pg.dropped.3........" - NULL,
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
| mothballed | Mothballed |
| commissioning | Commissioning |
| cancelled | Cancelled |
| maturing | Maturing |
| construction | Construction |

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
| None | 2020\-12\-09 01:46:29\.671803\+00:00 | 2022\-10\-04 06:24:39\.132031\+00:00 | hydro | Hyrdo | True | hydro |
| None | 2020\-12\-09 01:46:29\.904852\+00:00 | 2022\-10\-04 06:24:39\.329845\+00:00 | solar\_rooftop | Solar \(Rooftop\) | True | solar |
| None | 2020\-12\-09 01:46:29\.145850\+00:00 | 2022\-10\-04 06:24:38\.667053\+00:00 | bioenergy\_biomass | Biomass | False | bioenergy |
| None | 2020\-12\-09 01:46:30\.020865\+00:00 | None | aggregator\_vpp | Aggregator \(VPP\) | True | None |
| None | 2020\-12\-09 01:46:29\.261797\+00:00 | 2022\-10\-04 06:24:38\.765765\+00:00 | coal\_brown | Coal \(Brown\) | False | coal |

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
| None | 2022\-10\-04 06:24:38\.163568\+00:00 | 2024\-08\-13 02:51:57\.473752\+00:00 | solar | Solar | \#FED500 | True |
| None | 2022\-10\-04 06:24:38\.114476\+00:00 | 2024\-08\-13 02:51:57\.357664\+00:00 | wind | Wind | \#417505 | True |
| None | 2022\-10\-04 06:24:38\.013420\+00:00 | None | coal | Coal | \#4a4a4a | False |
| None | 2022\-10\-04 06:24:38\.363459\+00:00 | None | distillate | Distillate | \#F35020 | False |
| None | 2022\-10\-04 06:24:38\.313712\+00:00 | 2024\-08\-13 02:51:57\.750658\+00:00 | hydro | Hyrdo | \#4582B4 | True |

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
| 4888 | None | None | Lonsdale | SA | 5160 | None | False | False | None | None | 0101000020E61000004ACE396D7D4F6140146384CC688C41C0 | None | None |
| 13664 |  |  |  | TAS | None | None | True | False | None | opennem\.registry | 0101000020E6100000FF5FF466945D624099089CA30CE744C0 | None | None |
| 13801 | None | None | None | NSW | None | None | False | False | None | None | None | None | None |
| 13579 |  |  |  | NSW | None | None | True | False | None | opennem\.registry | 0101000020E6100000D7FA22A12D9462408A389D64AB3742C0 | None | None |
| 13508 |  |  |  | VIC | None | None | True | False | None | opennem\.registry | 0101000020E6100000959F54FBF40C6240757286E28E0743C0 | None | None |

## Table: public.milestones

Total rows: 14,464

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
    "........pg.dropped.4........" - NULL,
    significance integer NOT NULL,
    value double precision NOT NULL,
    "........pg.dropped.7........" - NULL,
    network_id text NULL,
    fueltech_id text NULL,
    description character varying NULL,
    period character varying NULL,
    "........pg.dropped.12........" - NULL,
    "........pg.dropped.13........" - NULL,
    aggregate character varying NOT NULL,
    metric character varying NULL,
    value_unit character varying NULL,
    description_long character varying NULL,
    network_region text NULL,
    "........pg.dropped.19........" - NULL,
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
| b9c0d585\-2ca5\-46c9\-a7d7\-69fdd995dcef | au\.wem\.solar\.energy\.day\.high | 2015\-11\-10 00:00:00 | 9 | 2579\.9138 | WEM | solar | Daily solar energy high record for WEM | day | high | energy | MWh | None | None | 847aefe9\-d71c\-4763\-bd03\-5103f9b80d88 |
| dc1d0f13\-32b0\-4877\-b9df\-d2dad286eef3 | au\.nem\.nsw1\.hydro\.power\.interval\.low | 2001\-12\-23 02:50:00 | 1 | \-69\.98 | NEM | hydro | Interval hyrdo power low record for NEM in New South Wales | interval | low | power | MW | None | NSW1 | 7f6a907e\-01a5\-4f31\-9c32\-bb99878dd497 |
| 0f9be28d\-47d8\-4978\-8414\-51c1ff8d6ff4 | au\.nem\.nsw1\.solar\.energy\.month\.high | 2015\-09\-01 00:00:00 | 9 | 26017\.5473 | NEM | solar | Monthly solar energy high record for NEM in New South Wales | month | high | energy | MWh | None | NSW1 | 72fa2da5\-b8f2\-4cdb\-b0c8\-13b71855e0d9 |
| 82f9de73\-6278\-4baf\-a1d5\-6963e966cc15 | au\.nem\.tas1\.hydro\.power\.interval\.high | 2005\-06\-20 17:25:00 | 4 | 1498\.38 | NEM | hydro | Interval hyrdo power high record for NEM in Tasmania | interval | high | power | MW | None | TAS1 | cd5e1252\-95f4\-477e\-9285\-b14bc10616f4 |
| 34274b4b\-ba1a\-4a15\-a9c1\-28b16ee08126 | au\.nem\.qld1\.coal\.power\.interval\.high | 1998\-12\-16 09:30:00 | 4 | 5333\.0 | NEM | coal | Interval coal power high record for NEM in Queensland | interval | high | power | MW | None | QLD1 | f1ba0c10\-72e9\-4190\-8364\-1500a6e91c00 |

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
    created_by text NULL,
    created_at timestamp with time zone NULL,
    updated_at timestamp with time zone NULL,
    code text NOT NULL,
    country text NOT NULL,
    label text NULL,
    timezone text NOT NULL,
    interval_size integer NOT NULL,
    "offset" integer NULL,
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
| None | 2024\-08\-10 04:32:14\.380672\+00:00 | None | WEMDE | au | WEMDE | Australia/Perth | 5 | 480 | AWST | True | 0 | WEMDE | None | None |
| None | 2021\-04\-09 10:15:56\.408641\+00:00 | 2024\-08\-10 04:32:14\.576316\+00:00 | AEMO\_ROOFTOP | au | AEMO Rooftop | Australia/Brisbane | 30 | 600 | AEST | False | 0 | NEM | 2016\-07\-31 14:30:00\+00:00 | 2024\-08\-02 23:30:00\+00:00 |
| None | 2020\-12\-09 01:46:31\.118850\+00:00 | 2024\-08\-02 04:15:22\.375279\+00:00 | WEM | au | WEM | Australia/Perth | 30 | 480 | AWST | True | 0 | WEM | 2006\-09\-19 16:00:00\+00:00 | 2024\-08\-01 23:55:00\+00:00 |
| None | 2020\-12\-09 01:46:31\.176786\+00:00 | 2024\-08\-03 00:15:22\.319623\+00:00 | APVI | au | APVI | Australia/Perth | 15 | 600 | AWST | False | 0 | WEM | 2015\-03\-19 20:15:00\+00:00 | 2024\-08\-03 00:00:00\+00:00 |
| None | 2023\-02\-22 09:54:49\.679305\+00:00 | 2024\-08\-10 04:32:14\.781558\+00:00 | OPENNEM\_ROOFTOP\_BACKFILL | au | OpenNEM Rooftop Backfill | Australia/Brisbane | 30 | 600 | AEST | False | 0 | NEM | 2015\-03\-19 20:15:00\+00:00 | 2018\-02\-28 09:30:00\+00:00 |

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
    created_by text NULL,
    created_at timestamp with time zone NULL,
    updated_at timestamp with time zone NULL,
    network_id text NOT NULL,
    code text NOT NULL,
    timezone text NULL,
    timezone_database text NULL,
    "offset" integer NULL,
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
| None | 2020\-12\-09 01:46:31\.422815\+00:00 | None | NEM | VIC1 | None | None | None | True |
| None | 2020\-12\-09 01:46:31\.363840\+00:00 | None | NEM | QLD1 | None | None | None | True |
| None | 2024\-08\-10 04:32:14\.952549\+00:00 | None | WEM | WEMDE | None | None | None | True |
| None | 2020\-12\-09 01:46:31\.540863\+00:00 | None | NEM | SA1 | None | None | None | True |
| None | 2020\-12\-09 01:46:31\.302424\+00:00 | None | NEM | NSW1 | None | None | None | True |

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
    "........pg.dropped.1........" - NULL,
    "........pg.dropped.2........" - NULL,
    "........pg.dropped.3........" - NULL,
    id integer NOT NULL,
    code text NULL,
    name text NULL,
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

| id | code | name | network\_name | network\_code | country | abn | approved | approved\_by | approved\_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 161 | Padgold | PaddingtonGold | None | None | None | None | False | None | None |
| 17 | MPOWER | MetroPowerCompanyPtyltd | Metro Power Company Pty Ltd | None | None | None | False | None | 2021\-01\-15 04:20:48\.579016\+00:00 |
| 119 | Enernoc | EnerNOCAustralia | None | None | None | None | False | None | None |
| 95 | Astar | AStarElectricity | None | None | None | None | False | None | None |
| 170 | Skyfrm | SkyFarming | None | None | None | None | False | None | None |

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
    created_by text NULL,
    created_at timestamp with time zone NULL,
    updated_at timestamp with time zone NULL,
    id integer NOT NULL,
    participant_id integer NULL,
    location_id integer NULL,
    code text NOT NULL,
    name text NULL,
    description text NULL,
    wikipedia_link text NULL,
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

| created\_by | created\_at | updated\_at | id | participant\_id | location\_id | code | name | description | wikipedia\_link | wikidata\_id | network\_code | network\_name | approved | approved\_by | approved\_at | website\_url |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| opennem\.registry | 2020\-12\-09 15:32:39\.826093\+00:00 | 2024\-06\-07 13:12:27\.883559\+00:00 | 351 | None | 13766 | WYNDW | Wyndham | None | None | None | None | Wyndham | True | opennem\.importer\.facilities | 2024\-06\-07 23:12:27\.926969\+00:00 | None |
| opennem\.registry | 2020\-12\-09 15:32:39\.826093\+00:00 | 2024\-06\-07 13:11:39\.752649\+00:00 | 105 | None | 13520 | DDSF | Darling Downs | Darling Downs Solar Farm is a 110MW photovoltaic solar power station in Queensland, Australia developed by APA Group 45 km west of Dalby in the Darling Downs region next to the Darling Downs Power Sta\.\.\. | https://en\.wikipedia\.org/wiki/Darling\_Downs\_Solar\_Farm | Q56276276 | None | Darling Downs | True | opennem\.importer\.facilities | 2024\-06\-07 23:11:39\.795911\+00:00 | None |
| opennem\.registry | 2020\-12\-09 15:32:39\.826093\+00:00 | 2024\-06\-07 13:12:15\.152078\+00:00 | 93 | None | 13508 | CORIO | Corio | None | None | None | None | Corio | True | opennem\.importer\.facilities | 2024\-06\-07 23:12:15\.199212\+00:00 | None |
| opennem\.registry | 2020\-12\-09 15:32:39\.826093\+00:00 | 2024\-06\-07 13:11:29\.688888\+00:00 | 279 | None | 13694 | SNOWY3 | Guthega | Guthega Power Station is located in the Snowy Mountains region of New South Wales, Australia\. The power station's purpose is for the generation of electricity\. It is the first to be completed and smal\.\.\. | https://en\.wikipedia\.org/wiki/Guthega\_Power\_Station | Q5621737 | None | Guthega | True | opennem\.importer\.facilities | 2024\-06\-07 23:11:29\.768131\+00:00 | None |
| opennem\.init | 2021\-01\-18 08:28:25\.570778\+00:00 | 2024\-06\-07 13:12:33\.794361\+00:00 | 439 | None | 1639 | MERSOLAR | Merredin | Merredin Solar Farm is the largest solar farm in Western Australia and will have an expected output of 281GWh of electricity annually, generating enough energy to power approximately 42,000 Western Au\.\.\. | None | None | None | Merredin Solar Farm | True | opennem\.importer\.facilities | 2024\-06\-07 23:12:33\.844438\+00:00 | None |

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
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 2017\-09\-30 00:00:00\+00:00 | au | CPI | 111\.4 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 1987\-06\-30 00:00:00\+00:00 | au | CPI | 46\.0 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 1985\-12\-31 00:00:00\+00:00 | au | CPI | 40\.5 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 1989\-12\-31 00:00:00\+00:00 | au | CPI | 55\.2 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 1937\-12\-01 00:00:00\+00:00 | au | CPI | 2\.5 |

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
| 16cfc8fc\-bd8f\-47db\-9a38\-8bcda2b153e9 | wem\_per\_interval\_check | 2024\-06\-02 10:53:16\.421856\+00:00 | 2024\-06\-02 10:53:33\.507213\+00:00 | None | None | 0 | forever | noisy |  |
| 91fa3b74\-ce93\-48f4\-a147\-d052cb14563d | run\_aggregate\_flow\_for\_interval\_v3 | 2024\-03\-25 23:55:03\.091450\+00:00 | 2024\-03\-25 23:55:03\.191689\+00:00 | None | None | 0 | forever | info |  |
| b974511f\-abf9\-40d7\-a315\-d5e4f6be1932 | run\_flows\_for\_last\_intervals | 2024\-06\-02 17:00:02\.056523\+00:00 | 2024\-06\-02 17:00:03\.021863\+00:00 | None | None | 0 | forever | info |  |
| 580e29d3\-5f94\-4b1a\-906f\-fc392c6fbf58 | wem\_per\_interval\_check | 2024\-07\-01 23:50:13\.134801\+00:00 | 2024\-07\-01 23:50:25\.486808\+00:00 | None | None | 0 | forever | noisy |  |
| e1cb0308\-b9c0\-4c97\-a6fe\-592c3fbf85ac | run\_aggregate\_flow\_for\_interval\_v3 | 2024\-06\-28 07:10:01\.502779\+00:00 | 2024\-06\-28 07:10:01\.559125\+00:00 | None | None | 0 | forever | info |  |
