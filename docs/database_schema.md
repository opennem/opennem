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
| public | [balancing_summary](#public-balancing-summary) | 11,329,335 |
| public | [bom_observation](#public-bom-observation) | 5,920,234 |
| public | [bom_station](#public-bom-station) | 773 |
| public | [crawl_history](#public-crawl-history) | 791,707 |
| public | [crawl_meta](#public-crawl-meta) | 50 |
| public | [facility](#public-facility) | 787 |
| public | [facility_scada](#public-facility-scada) | 769,754,406 |
| public | [facility_status](#public-facility-status) | 12 |
| public | [feedback](#public-feedback) | 94 |
| public | [fueltech](#public-fueltech) | 26 |
| public | [fueltech_group](#public-fueltech-group) | 10 |
| public | [location](#public-location) | 551 |
| public | [milestones](#public-milestones) | 18,679 |
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
| 117843 | PRICES UNCHANGED | 2024\-08\-27 12:10:17 | 2024\-08\-27 00:00:00 | \[EventId:202408271150\_confirmed\] Prices for interval 27\-Aug\-2024 11:50 are now confirmed | AEMO ELECTRICITY MARKET NOTICE

Issued by Australian Energy Market Operator Ltd at 1210 hrs on 27 August 2024

PRICES ARE NOW CONFIRMED for trading interval 27\-Aug\-2024 11:50\.

In accordance with Mark\.\.\. |
| 117966 | RECLASSIFY CONTINGENCY | 2024\-08\-29 19:29:33 | 2024\-08\-29 00:00:00 | Reclassification of a Non\-Credible Contingency Event: Para\-Templers West and Magill\-Torrens Island A 275kV lines in SA due to severe weather warning\. | AEMO ELECTRICITY MARKET NOTICE\.

Reclassification of a non\-credible contingency event as a credible contingency event due to severe weather warning\.

AEMO considers the simultaneous trip of the follow\.\.\. |
| 117976 | RECLASSIFY CONTINGENCY | 2024\-08\-29 23:09:34 | 2024\-08\-29 00:00:00 | Reclassification of non\-credible contingency event due to existence of widespread abnormal conditions \- SA region\. | AEMO ELECTRICITY MARKET NOTICE\.

AEMO has identified that a non\-credible contingency event impacting the power system is more likely to occur and is considered reasonably possible because of the exist\.\.\. |
| 117322 | LOAD RESTORE | 2024\-07\-08 19:34:37 | 2024\-07\-08 00:00:00 | Load Restoration Direction in the NSW Region | AEMO has directed load restoration commencing at 1930 hrs 08/07/2024 in the NSW region\. The direction was issued under section 116 of the NEL, and was a clause 4\.8\.9 instruction under the NER\. |
| 117679 | NON\-CONFORMANCE | 2024\-08\-15 10:10:17 | 2024\-08\-15 00:00:00 | NON\-CONFORMANCE Region SA1 Thursday, 15 August 2024 | AEMO has declared the following units comprising an Aggregate Dispatch Group as non\-conforming under clause 3\.8\.23 of the National Electricity Rules:

Units:      TB2BG1, TB2BL1
Aggregate Dispatch Gro\.\.\. |

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
| 2021\-05\-24 00:00:00\+00:00 | NEM | HDWF1 | wind | 1739\.720833333333352 | 30489\.54814833333440769837 | 0E\-16 | SA1 |
| 2019\-10\-25 00:00:00\+00:00 | NEM | LYA3 | coal\_brown | 13435\.5000000000006 | 943126\.475090416708548939 | 15515\.552536575000692890590 | VIC1 |
| 2019\-05\-25 00:00:00\+00:00 | NEM | BW01 | coal\_black | 14407\.61569625000004 | 1006923\.1375886684663436359 | 13149\.0113407865723365057248 | NSW1 |
| 2017\-07\-31 00:00:00\+00:00 | NEM | FISHER | hydro | 1101\.203750000000019 | 131679\.62517122500422260135 | 0E\-16 | TAS1 |
| 2024\-07\-28 00:00:00\+00:00 | NEM | TRIBUTE | hydro | 1778\.3316516666666630 | 290224\.99202610277692141355547222222195 | 0E\-17 | TAS1 |

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
| 2014\-10\-16 00:00:00\+00:00 | WEM | WEM | None | None |
| 2023\-11\-18 00:00:00\+00:00 | NEM | TAS1 | 27\.50894312166666666656 | 1984162\.8094048727583269684777000 |
| 2006\-08\-08 00:00:00\+00:00 | NEM | SNOWY1 | 1\.53081166666666666673 | 8651\.5850499999999997383000 |
| 2001\-07\-06 00:00:00\+00:00 | NEM | TAS1 | None | None |
| 2017\-12\-08 00:00:00\+00:00 | WEM | WEM | None | None |

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
| 2024\-06\-30 23:35:00\+00:00 | NEM | NSW1 | 4\.966675 | 21\.082073333333334 | 3\.7115070128399066 | 15\.159561332198063 | 0\.0 | 0\.0 |
| 2009\-08\-31 02:35:00\+00:00 | NEM | SA1 | 3\.9166666666666665 | 0\.0 | 4\.791348112896432 | 0\.0 | 0\.0 | 0\.0 |
| 2021\-04\-02 00:40:00\+00:00 | NEM | TAS1 | 36\.375 | 0\.0 | 34\.52095286842251 | 0\.0 | 0\.0 | 0\.0 |
| 2009\-09\-11 08:55:00\+00:00 | NEM | VIC1 | 8\.083333333333334 | 60\.083333333333336 | 0\.0 | 71\.23381391272599 | 0\.0 | 0\.0 |
| 2021\-10\-05 03:30:00\+00:00 | NEM | SA1 | 0\.0 | 17\.6599525 | 0\.0 | 0\.8907498400159755 | 0\.0 | 0\.0 |

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

Total rows: 11,329,340

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
| 2015\-09\-03 09:05:00 | NEM | VIC1 | None | None | None | None | None | False | \-52\.82 | 6198\.05 | 43\.95049 | None | 5871\.36 |
| 2014\-07\-20 23:45:00 | NEM | QLD1 | None | None | None | None | None | False | 1027\.41 | 5489\.51282 | 27\.74685 | None | 5361\.01 |
| 2014\-12\-20 14:55:00 | NEM | NSW1 | None | None | None | None | None | False | \-1382\.86 | 7344\.08357 | 28\.18006 | None | 7320\.3 |
| 2003\-01\-15 17:00:00 | NEM | SNOWY1 | None | None | None | None | 25\.15 | False | 992\.92 | 7\.08 | None | 992\.92 | None |
| 2000\-09\-08 09:30:00 | NEM | NSW1 | None | None | None | None | 56\.62 | False | \-126\.92 | 9229\.37 | None | \-126\.92 | None |

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
| 2015\-06\-02 22:00:00\+00:00 | 040913 | 7\.5 | 8\.8 | None | None | None | None | None | 9\.3 | None | None | None |
| 2021\-01\-22 10:20:00\+00:00 | 250070 | 26\.0 | 27\.9 | 1013\.1 | WNW | 2 |  |  | 20 | 4 | None | None |
| 2021\-01\-28 12:00:00\+00:00 | 061412 | 22\.4 | 19\.6 | 1019\.7 | S | 2 |  |  | 95 | 6 | None | None |
| 2022\-02\-10 13:00:00\+00:00 | 094029 | 12\.3 | 15\.5 | 1017\.2 | NW | 13\.0 | None | None | 56\.0 | 24\.0 | None | None |
| 2021\-03\-29 13:30:00\+00:00 | 200731 | 31\.3 | 28\.2 | 1008\.4 | ESE | 13 |  |  | 76 | 28 | None | None |

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
| 040405 | QLD | HERVEY BAY AIRPORT | None | 0101000020E61000005C8FC2F5281C634052B81E85EB5139C0 | http://www\.bom\.gov\.au/fwo/IDQ60801/IDQ60801\.95565\.json | False | Hervey Bay | 5 | http://www\.bom\.gov\.au/products/IDQ60801/IDQ60801\.95565\.shtml | 12 | None |
| 008296 | WA | MORAWA AIRPORT | None | 0101000020E6100000E17A14AE47015D403333333333333DC0 | http://www\.bom\.gov\.au/fwo/IDW60801/IDW60801\.94417\.json | False | Morawa Airport | 5 | http://www\.bom\.gov\.au/products/IDW60801/IDW60801\.94417\.shtml | 271 | None |
| 089002 | VIC | BALLARAT AERODROME | None | 0101000020E6100000E17A14AE47F96140E17A14AE47C142C0 | http://www\.bom\.gov\.au/fwo/IDV60801/IDV60801\.94852\.json | False | Ballarat | 5 | http://www\.bom\.gov\.au/products/IDV60801/IDV60801\.94852\.shtml | 435 | None |
| 018120 | SA | WHYALLA AERO | None | 0101000020E6100000713D0AD7A330614066666666668640C0 | http://www\.bom\.gov\.au/fwo/IDS60801/IDS60801\.95664\.json | False | Whyalla | 5 | http://www\.bom\.gov\.au/products/IDS60801/IDS60801\.95664\.shtml | 9 | None |
| 018069 | SA | ELLISTON | None | 0101000020E610000014AE47E17ADC60403333333333D340C0 | http://www\.bom\.gov\.au/fwo/IDS60801/IDS60801\.94656\.json | False | Elliston | 5 | http://www\.bom\.gov\.au/products/IDS60801/IDS60801\.94656\.shtml | 7 | None |

## Table: public.crawl_history

Total rows: 791,711

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
| nemweb | au\.nemweb\.trading\_is | NEM | 2023\-07\-25 07:30:00\+00:00 | 5 | None | 2023\-07\-24 21:30:06\+00:00 |
| nemweb | au\.nemweb\.trading\_is | NEM | 2023\-03\-12 05:20:00\+00:00 | 5 | None | 2023\-03\-11 19:20:14\+00:00 |
| nemweb | au\.nemweb\.dispatch\_scada | NEM | 2023\-09\-25 19:50:00\+00:00 | 445 | None | 2023\-09\-25 09:50:01\+00:00 |
| nemweb | au\.nemweb\.current\.dispatch\_is | NEM | 2024\-04\-01 08:05:00\+00:00 | 16 | None | 2024\-03\-31 22:05:02\+00:00 |
| nemweb | au\.nemweb\.dispatch\_scada | NEM | 2023\-09\-18 11:35:00\+00:00 | 446 | None | 2023\-09\-19 22:00:27\+00:00 |

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
| au\.nemweb\.rooftop\_forecast | \{'version': '2', 'last\_crawled': '2023\-09\-26T16:30:53\+10:00', 'server\_latest': '2023\-10\-04T04:00:00\+10:00', 'latest\_processed': '2023\-10\-04T04:00:00\+10:00'\} | 2022\-06\-25 06:33:16\.514160\+00:00 | 2023\-09\-26 06:30:57\.489743\+00:00 |
| apvi\.year\.data | \{'version': '2', 'last\_crawled': '2024\-01\-16T10:17:58\+11:00', 'server\_latest': '2024\-01\-16T09:00:00\+10:00', 'latest\_processed': '2024\-01\-16T09:00:00\+10:00'\} | 2023\-09\-01 04:07:46\.172556\+00:00 | 2024\-01\-15 23:30:22\.912226\+00:00 |
| au\.nem\.current\.dispatch\_scada | \{'version': '2', 'last\_crawled': '2022\-06\-27T11:25:10\+10:00', 'server\_latest': '2022\-06\-27T11:25:00\+10:00', 'latest\_processed': '2022\-06\-27T11:25:00\+10:00'\} | 2022\-06\-10 07:34:07\.936856\+00:00 | 2022\-06\-27 01:37:48\.310364\+00:00 |
| au\.wemde\.current\.trading\_report | \{'last\_crawled': '2024\-08\-08T11:40:04\+10:00', 'latest\_interval': '2024\-08\-08T07:30:00\+08:00', 'latest\_processed': '2024\-01\-15T11:46:08\+11:00'\} | 2024\-01\-14 20:44:28\.291724\+00:00 | 2024\-08\-08 01:40:04\.645263\+00:00 |
| au\.nemweb\.current\.dispatch\_is | \{'version': '2', 'last\_crawled': '2024\-09\-14T08:05:30\+10:00', 'server\_latest': '2024\-08\-03T10:50:00\+10:00', 'latest\_processed': '2024\-08\-03T10:50:00\+10:00'\} | 2023\-09\-04 10:39:36\.962104\+00:00 | 2024\-09\-13 22:05:30\.508699\+00:00 |

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
| opennem\.registry | 2020\-12\-09 15:33:24\.727775\+00:00 | 2024\-06\-07 13:12:13\.892790\+00:00 | 95 | NEM | wind | operating | 73 | CBWF1 | NEM | VIC1 | None | True | GENERATOR | 19\.8 | None | None | None | None | None | None | True | None | 2020\-12\-09 15:33:24\.727755\+00:00 | 0\.0 | False | None | None | None | None | None | None | None | True |
| opennem\.registry | 2020\-12\-09 15:33:39\.852693\+00:00 | 2024\-06\-07 13:11:41\.702535\+00:00 | 184 | NEM | gas\_wcmg | operating | 136 | GROSV2 | NEM | QLD1 | None | True | GENERATOR | 15\.0 | None | None | None | None | None | None | True | None | 2020\-12\-09 15:33:39\.852680\+00:00 | 0\.716 | False | None | None | None | None | None | None | None | True |
| opennem\.init | 2023\-01\-09 03:15:16\.014461\+00:00 | 2024\-06\-07 13:12:39\.910630\+00:00 | 763 | NEM | solar\_utility | operating | 533 | NEWENSF2 | None | NSW1 | None | True | GENERATOR | 200\.0 | None | None | None | 144 | None | 1\.388 | False | None | None | 0\.0 | False | None | 2022\-12\-20 00:45:00\+00:00 | 2024\-08\-03 00:50:00\+00:00 | None | None | None | None | True |
| opennem\.registry | 2020\-12\-09 15:33:47\.441423\+00:00 | 2024\-06\-07 13:12:19\.277347\+00:00 | 222 | NEM | gas\_ocgt | operating | 162 | JLA03 | NEM | VIC1 | None | True | GENERATOR | 51\.0 | None | None | None | None | None | None | True | None | 2020\-12\-09 15:33:47\.441408\+00:00 | 0\.87940454 | False | None | 1998\-12\-10 01:25:00\+00:00 | 2024\-08\-02 09:25:00\+00:00 | None | None | None | None | True |
| opennem\.init | 2021\-07\-14 17:01:51\.418425\+00:00 | 2023\-06\-16 03:05:00\.834806\+00:00 | 707 | NEM | battery\_charging | operating | 65 | BULBESL1 | None | VIC1 | None | True | LOAD | 20\.0 | None | None | None | 40 | None | 0\.5 | True | None | None | 0\.0 | False | None | 2021\-07\-06 09:40:00\+00:00 | 2024\-08\-03 00:50:00\+00:00 | None | None | None | None | True |

## Table: public.facility_scada

Total rows: 769,754,881

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
| NEM | 2017\-03\-13 03:35:00 | W/HOE\#2 | 0\.0 | None | False | 1 | 0E\-20 |
| NEM | 2001\-11\-03 21:30:00 | DARTM1 | 124\.1 | None | False | 1 | 10\.3691666666666667 |
| NEM | 2018\-10\-31 03:05:00 | VPGS5 | 0\.0 | None | False | 1 | 0E\-20 |
| NEM | 2009\-09\-28 08:45:00 | LYA2 | 0\.0 | None | False | 1 | 0E\-20 |
| NEM | 2012\-04\-24 13:00:00 | DG\_QLD1 | 0\.0 | None | False | 1 | 0E\-20 |

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
| permitted | Permitted |
| cancelled | Cancelled |
| mothballed | Mothballed |
| committed | Committed |
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

### Sample Data

| id | subject | description | email | twitter | user\_ip | user\_agent | created\_at | alert\_sent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 64 | Shoalhaven facility feedback | 
\*\*No email provided\.\*\*
   

\*\*Path:\*\*
/facility/au/NEM/SHOALHAV/?range=3d&interval=30m

\*\*Sources:\*\*
https://en\.wikipedia\.org/wiki/Shoalhaven\_Scheme

\*\*Fields:\*\*

\`\`\`
\[\]
\`\`\`

\*\*Description:\*\*
The des\.\.\. | None | None | 172\.19\.0\.1 | Mozilla/5\.0 \(Windows NT 10\.0; Win64; x64\) AppleWebKit/537\.36 \(KHTML, like Gecko\) Chrome/115\.0\.0\.0 Safari/537\.36 | 2023\-08\-18 00:11:26\.418083\+00:00 | False |
| 30 | Bango facility feedback | 
\*\*No email provided\.\*\*
   

\*\*Path:\*\*
/facility/au/NEM/BANGOWF/?range=7d&interval=30m

\*\*Sources:\*\*
sdfsd

\*\*Fields:\*\*

\`\`\`
\[\]
\`\`\`

\*\*Description:\*\*
sdfsd
 | None | None | 61\.68\.241\.134 | Mozilla/5\.0 \(Macintosh; Intel Mac OS X 10\_15\_7\) AppleWebKit/537\.36 \(KHTML, like Gecko\) Chrome/91\.0\.4472\.124 Safari/537\.36 | 2021\-07\-03 05:51:43\.116520\+00:00 | True |
| 80 | Mt Piper facility feedback | 
\*\*Email:\*\*
mushalik@tpg\.com\.au     
   

\*\*Path:\*\*
/facility/au/NEM/MP/?range=3d&interval=30m

\*\*Sources:\*\*
https://opennem\.org\.au/facility/au/NEM/MP/?range=3d&interval=30m

\*\*Fields:\*\*

\`\`\`
\[\]
\`\`\`

\.\.\. | mushalik@tpg\.com\.au | None | 172\.19\.0\.1 | Mozilla/5\.0 \(Windows NT 10\.0; Win64; x64\) AppleWebKit/537\.36 \(KHTML, like Gecko\) Chrome/120\.0\.0\.0 Safari/537\.36 | 2023\-12\-16 00:49:51\.059202\+00:00 | False |
| 70 | Rye Park facility feedback | 
\*\*No email provided\.\*\*
   

\*\*Path:\*\*
/facility/au/NEM/RYEPARK/?range=1d&interval=30m

\*\*Sources:\*\*
12:00 am on 8 Oct

\*\*Fields:\*\*

\`\`\`
\[\]
\`\`\`

\*\*Description:\*\*
Is this solar or wind?
 | None | None | 172\.19\.0\.1 | Mozilla/5\.0 \(Macintosh; Intel Mac OS X 10\_15\_7\) AppleWebKit/605\.1\.15 \(KHTML, like Gecko\) Version/17\.0\.1 Safari/605\.1\.15 | 2023\-10\-08 00:12:27\.297574\+00:00 | False |
| 76 | Mannum facility feedback | 
\*\*No email provided\.\*\*
   

\*\*Path:\*\*
/facility/au/NEM/MAPS2/?range=3d&interval=30m

\*\*Sources:\*\*
\.

\*\*Fields:\*\*

\`\`\`
\[
 \{
  "key": "Facility default map",
  "value": \{
   "type": "Point",
   "coordi\.\.\. | None | None | 172\.19\.0\.1 | Mozilla/5\.0 \(Windows NT 10\.0; Win64; x64\) AppleWebKit/537\.36 \(KHTML, like Gecko\) Chrome/120\.0\.0\.0 Safari/537\.36 Edg/120\.0\.0\.0 | 2023\-12\-11 04:02:14\.431582\+00:00 | False |

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
| None | 2020\-12\-09 01:46:29\.552866\+00:00 | 2022\-10\-04 06:24:39\.023691\+00:00 | gas\_steam | Gas \(Steam\) | False | gas |
| None | 2020\-12\-09 01:46:29\.492808\+00:00 | 2022\-10\-04 06:24:38\.971553\+00:00 | gas\_recip | Gas \(Reciprocating\) | False | gas |
| None | 2020\-12\-09 01:46:29\.671803\+00:00 | 2022\-10\-04 06:24:39\.132031\+00:00 | hydro | Hyrdo | True | hydro |
| None | 2020\-12\-09 01:46:28\.964818\+00:00 | 2022\-10\-04 06:24:38\.513422\+00:00 | battery\_charging | Battery \(Charging\) | True | battery\_charging |
| None | 2021\-03\-25 10:35:29\.547107\+00:00 | None | interconnector | Interconnector | False | None |

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
| None | 2022\-10\-04 06:24:38\.263261\+00:00 | 2024\-08\-13 02:51:57\.662572\+00:00 | battery\_discharging | Battery \(Discharging\) | \#00A2FA | True |
| None | 2022\-10\-04 06:24:38\.054393\+00:00 | None | gas | Gas | \#FF8813 | False |
| None | 2022\-10\-04 06:24:38\.214596\+00:00 | 2024\-08\-13 02:51:57\.574303\+00:00 | battery\_charging | Battery \(Charging\) | \#B2DAEF | True |
| None | 2022\-10\-04 06:24:38\.461796\+00:00 | 2024\-08\-13 02:51:57\.973473\+00:00 | pumps | Pumps | \#88AFD0 | True |
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
| 13482 |  |  |  | TAS | None | None | True | False | None | opennem\.registry | 0101000020E6100000846B865763486240FCACD18C302245C0 | None | None |
| 823 | None | None | Breadalbane | NSW | 2581 | None | False | False | None | None | 0101000020E61000008467268CB2AC6240A1AE4EDA746941C0 | None | None |
| 13463 |  |  |  | NSW | None | None | True | False | None | opennem\.registry | 0101000020E6100000C8409E5DBEAE6240E529ABE97A2C40C0 | None | None |
| 13605 |  |  |  | VIC | None | None | True | False | None | opennem\.registry | 0101000020E6100000DD67E82DBD52624082BEE697762043C0 | None | None |
| 13498 |  |  |  | QLD | None | None | True | False | None | opennem\.registry | 0101000020E610000095E35F15797162409E126B4CE3D636C0 | None | None |

## Table: public.milestones

Total rows: 18,684

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
| 5396ad69\-0b89\-4e38\-ada3\-595594244e63 | au\.nem\.sa1\.gas\.energy\.week\.low | 2022\-12\-12 00:00:00 | 6 | 16157\.0303 | NEM | gas | Weekly gas energy low record for NEM in South Australia | week | low | energy | MWh | None | SA1 | e19ae7a1\-f9e5\-415b\-b552\-18f40b0f2b29 |
| ba688fd9\-10ab\-4534\-a42f\-647c5e3684fa | au\.nem\.sa1\.solar\.power\.interval\.high | 2016\-08\-16 12:30:00 | 4 | 795\.4814725945301 | NEM | solar | Interval solar power high record for NEM in South Australia | interval | high | power | MW | None | SA1 | 45f00b7e\-c14e\-414b\-b50e\-1affd2299cd0 |
| e6c6c740\-9d7f\-4429\-a850\-9f33801d3b57 | au\.nem\.coal\.emissions\.week\.low | 2015\-07\-27 00:00:00 | 6 | 3159335\.1314 | NEM | coal | Weekly coal emissions low record for NEM | week | low | emissions | tCO2e | None | None | ecf540f8\-9584\-4c7a\-a72c\-41d00f530c46 |
| 3d66d0a6\-2d69\-46c9\-a446\-01186e56db44 | au\.nem\.vic1\.gas\.emissions\.day\.high | 2017\-04\-06 00:00:00 | 8 | 15484\.0717 | NEM | gas | Daily gas emissions high record for NEM in Victoria | day | high | emissions | tCO2e | None | VIC1 | dd5e53c5\-d2b0\-4f54\-ba25\-36efab77290a |
| 9e686aba\-8817\-4c08\-8d32\-5518264d85ed | au\.nem\.tas1\.distillate\.power\.interval\.high | 2016\-04\-21 17:00:00 | 4 | 79\.344501 | NEM | distillate | Interval distillate power high record for NEM in Tasmania | interval | high | power | MW | None | TAS1 | 8a6792aa\-524e\-4fe3\-a885\-2cdd2c22c5b9 |

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
| None | 2023\-02\-22 09:54:49\.679305\+00:00 | 2024\-08\-10 04:32:14\.781558\+00:00 | OPENNEM\_ROOFTOP\_BACKFILL | au | OpenNEM Rooftop Backfill | Australia/Brisbane | 30 | 600 | AEST | False | 0 | NEM | 2015\-03\-19 20:15:00\+00:00 | 2018\-02\-28 09:30:00\+00:00 |
| None | 2020\-12\-09 01:46:31\.057929\+00:00 | 2024\-08\-10 04:32:14\.138129\+00:00 | NEM | au | NEM | Australia/Brisbane | 5 | 600 | AEST | True | 5 | NEM | 1998\-12\-06 15:40:00\+00:00 | 2024\-08\-03 00:15:00\+00:00 |
| None | 2021\-04\-12 07:06:18\.835747\+00:00 | 2024\-08\-10 04:32:14\.674557\+00:00 | AEMO\_ROOFTOP\_BACKFILL | au | AEMO Rooftop Backfill | Australia/Brisbane | 30 | 600 | AEST | False | 0 | NEM | None | None |
| None | 2020\-12\-09 01:46:31\.118850\+00:00 | 2024\-08\-02 04:15:22\.375279\+00:00 | WEM | au | WEM | Australia/Perth | 30 | 480 | AWST | True | 0 | WEM | 2006\-09\-19 16:00:00\+00:00 | 2024\-08\-01 23:55:00\+00:00 |
| None | 2024\-08\-10 04:32:14\.380672\+00:00 | None | WEMDE | au | WEMDE | Australia/Perth | 5 | 480 | AWST | True | 0 | WEMDE | None | None |

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
| None | 2024\-08\-10 04:32:14\.952549\+00:00 | None | WEM | WEMDE | None | None | None | True |
| None | 2020\-12\-09 01:46:31\.422815\+00:00 | None | NEM | VIC1 | None | None | None | True |
| None | 2020\-12\-09 01:46:31\.540863\+00:00 | None | NEM | SA1 | None | None | None | True |
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
| 101 | Byford1 | ByfordSolarFarm1 | None | None | None | None | False | None | None |
| 32 | WGRES | WasteGasResourcesPty | Waste Gas Resources Pty Ltd | None | None | None | False | None | 2021\-01\-15 04:20:49\.007619\+00:00 |
| 45 | BYFORD3 | ByfordSolarFarm3Pty | None | None | None | None | False | None | None |
| 184 | Uon | UON | None | None | None | None | False | None | None |
| 200 | Wpso | WesternPower | None | None | None | None | False | None | None |

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
| opennem\.registry | 2020\-12\-09 15:32:39\.826093\+00:00 | 2024\-06\-07 13:12:08\.133021\+00:00 | 202 | None | 13617 | MEADOWBK | Meadowbank | The Meadowbank Power Station is a run\-of\-the\-river hydroelectric power station located in the Central Highlands region of Tasmania, Australia\. The power station is situated on the  Lower River Derwent\.\.\. | https://en\.wikipedia\.org/wiki/Meadowbank\_Power\_Station | Q6803307 | None | Meadowbank | True | opennem\.importer\.facilities | 2024\-06\-07 23:12:08\.200300\+00:00 | None |
| opennem\.registry | 2020\-12\-09 15:32:39\.826093\+00:00 | 2024\-06\-07 13:12:30\.643858\+00:00 | 389 | None | 13402 | BLAIRFOX\_KARAKIN | Karakin | None | None | None | None | Karakin | True | opennem\.importer\.facilities | 2024\-06\-07 23:12:30\.689835\+00:00 | None |
| opennem\.importer\.interconnectors | 2021\-01\-03 07:05:38\.698274\+00:00 | 2022\-08\-05 09:26:21\.770864\+00:00 | 436 | None | 1236 | T\-V\-MNSP1 | Basslink dc interconnector \(mnsp\) | None | None | None | T\-V\-MNSP1 | None | False | None | None | None |
| opennem\.registry | 2020\-12\-09 15:32:39\.826093\+00:00 | 2024\-06\-07 13:12:32\.134196\+00:00 | 382 | None | 13395 | GOSNELLS | Gosnells | None | None | None | None | Gosnells | True | opennem\.importer\.facilities | 2024\-06\-07 23:12:32\.177745\+00:00 | None |
| opennem\.importer\.rooftop | 2021\-04\-12 07:06:35\.843691\+00:00 | None | 473 | None | 4873 | ROOFTOP\_AEMO\_ROOFTOP\_BACKFILL\_NSW | Rooftop Solar NSW | Solar rooftop facilities for NSW | None | None | None | None | False |  | None | None |

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
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 1973\-06\-30 00:00:00\+00:00 | au | CPI | 11\.8 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 1949\-12\-01 00:00:00\+00:00 | au | CPI | 4\.1 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 1932\-06\-01 00:00:00\+00:00 | au | CPI | 2\.4 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 1950\-12\-01 00:00:00\+00:00 | au | CPI | 4\.6 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 1998\-09\-30 00:00:00\+00:00 | au | CPI | 67\.5 |

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
| 3f664a60\-ee07\-4d1c\-bf3a\-fbe86b565bd9 | wem\_per\_interval\_check | 2024\-06\-16 01:56:30\.302873\+00:00 | 2024\-06\-16 01:56:44\.376681\+00:00 | None | None | 0 | forever | noisy |  |
| d36593bc\-5240\-421c\-a92d\-ef80112e0855 | wem\_per\_interval\_check | 2024\-04\-29 20:09:16\.422199\+00:00 | 2024\-04\-29 20:09:33\.677493\+00:00 | None | None | 0 | forever | noisy |  |
| 2b85167e\-2bde\-4b8e\-8e79\-587c2cdb6567 | run\_aggregate\_flow\_for\_interval\_v3 | 2024\-07\-28 21:35:01\.360356\+00:00 | 2024\-07\-28 21:35:01\.450236\+00:00 | None | None | 0 | forever | info |  |
| 3c8b6a67\-37fa\-41ae\-84d4\-ccd23005327d | run\_aggregate\_flow\_for\_interval\_v3 | 2024\-05\-31 16:55:01\.970291\+00:00 | 2024\-05\-31 16:55:02\.063462\+00:00 | None | None | 0 | forever | info |  |
| a464d48b\-7f64\-41ea\-9578\-dafe26a93009 | wem\_per\_interval\_check | 2024\-03\-19 18:55:32\.783532\+00:00 | 2024\-03\-19 18:55:54\.007792\+00:00 | None | None | 0 | forever | noisy |  |
