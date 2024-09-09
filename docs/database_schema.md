# Database Schema

Database: opennem
PostgreSQL version: PostgreSQL 16.4 (Ubuntu 16.4-1.pgdg22.04+1) on x86_64-pc-linux-gnu, compiled by gcc (Ubuntu 11.4.0-1ubuntu1~22.04) 11.4.0, 64-bit

## Enabled PostgreSQL Plugins

| Plugin Name | Version |
|-------------|--------|
| hstore | 1.6 |
| pg_stat_statements | 1.9 |
| plpgsql | 1.0 |
| postgis | 3.4.2 |
| postgis_raster | 3.4.2 |
| postgis_topology | 3.4.2 |
| timescaledb | 2.16.1 |

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

```
notice_id | notice_type | creation_date | issue_date | external_reference | reason
------------------------------------------------------------------------------------------
117367 | MARKET INTERVENTION | 2024-07-19 15:38:52 | 2024-07-19 00:00:00 | Direction - SA region 19/07/2024 | AEMO ELECTRICITY MARKET NOTICE

Direction - SA region 19/07/2024

In accordance with section 116 of the National Electricity Law, AEMO has issued a direction to a participant in the SA region. For the...
118053 | RECLASSIFY CONTINGENCY | 2024-09-02 10:04:07 | 2024-09-02 00:00:00 | Cancellation of a Non-Credible Contingency Event: Farrell-John Butters line and Farrell-Rosebery-Newton-Queenstown line in TAS1 due to Lightning. | Cancellation of reclassification of a Non-Credible Contingency Event as a Credible Contingency Event due to Lightning. AEMO considers the simultaneous trip of the following circuits is no longer reaso...
117528 | MARKET SYSTEMS | 2024-08-01 15:52:53 | 2024-08-01 00:00:00 | CHG0091339 | Production | NSW Marketnet Router Replacement | Change Number: CHG0091339

Notification issued to: Market Notice

Notification Type: Initial

Change Type: Normal 

Service/ Component: Market Network

Change Title: NSW Marketnet Router Replacement

...
118117 | PRICES UNCHANGED | 2024-09-04 10:36:26 | 2024-09-04 10:10:00 | [EventId:202409041010_confirmed] Prices for interval 04-Sep-2024 10:10 are now confirmed | AEMO ELECTRICITY MARKET NOTICE

Issued by Australian Energy Market Operator Ltd at 1035 hrs on 4 September 2024

PRICES ARE NOW CONFIRMED for trading interval 04-Sep-2024 10:10.

In accordance with Ma...
117917 | RECLASSIFY CONTINGENCY | 2024-08-28 09:13:39 | 2024-08-28 00:00:00 | Reclassification of a Non-Credible Contingency Event: Norwood - Scottsdale 1 110kV line and Norwood-Derby-Scottsdale 110kV line in TAS1 due to Lightning. | AEMO ELECTRICITY MARKET NOTICE

Reclassification of a Non-Credible Contingency Event as a Credible Contingency Event due to Lightning. AEMO considers the simultaneous trip of the following circuits to...
```

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

```
version_num
---------------
6f0b9e05ba9f
```

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

```
keyid | description | revoked | created_at
------------------------------------------------------------
DQwfwdHCzjBmnM5yMgkAVg | opennem default | False | 2021-05-27 12:28:38.314071+00:00
```

## Table: at_facility_daily

Total rows: 2885368

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

```
trading_day | network_id | facility_code | fueltech_id | energy | market_value | emissions | network_region
------------------------------------------------------------------------------------------------------------------------
2023-11-25 00:00:00+00:00 | AEMO_ROOFTOP | ROOFTOP_NEM_TAS | solar_rooftop | 732.9395 | 13743.76238250000000000000 | 0.0000 | TAS1
2013-10-07 00:00:00+00:00 | NEM | LOYYB1 | coal_brown | 12087.36308041666716 | 602063.9408921960801203863 | 13791.9393399571841254038660 | VIC1
2010-11-24 00:00:00+00:00 | NEM | JLB02 | gas_ocgt | 0 | 0 | 0 | VIC1
2014-12-04 00:00:00+00:00 | NEM | BRAEMAR5 | gas_ocgt | 3369.24468083333329 | 114787.7056424019156390832 | 2234.286308439305971263864 | QLD1
2023-06-07 00:00:00+00:00 | NEM | BARCALDN | gas_ccgt | 0 | 0 | 0 | QLD1
```

## Table: at_network_demand

Total rows: 62753

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

```
trading_day | network_id | network_region | demand_energy | demand_market_value
---------------------------------------------------------------------------
2008-08-06 00:00:00+00:00 | NEM | QLD1 | 143.97324666666666666664 | 688431.4406749999999991395000
2018-12-04 00:00:00+00:00 | WEM | WEM | None | None
2014-09-23 00:00:00+00:00 | NEM | SA1 | 33.65633757250000000001 | 959640.9777583072333333840309000
2002-10-05 00:00:00+00:00 | NEM | SA1 | 5.55343833333333333332 | 168548.4598166666666662063000
2002-12-29 00:00:00+00:00 | NEM | QLD1 | 19.12284749999999999998 | 459637.7299833333333328563000
```

## Table: at_network_flows

Total rows: 7917760

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

```
trading_interval | network_id | network_region | energy_imports | energy_exports | emissions_imports | emissions_exports | market_value_imports | market_value_exports
---------------------------------------------------------------------------------------------------------------------------------------
2013-05-05 16:05:00+00:00 | NEM | NSW1 | 105.810415 | 0.0 | 114.11639047319403 | 0.0 | 0.0 | 0.0
2014-11-15 19:45:00+00:00 | NEM | VIC1 | 22.555905 | 115.32772333333332 | 8.432016923007547 | 133.70293417810853 | 0.0 | 0.0
2010-09-14 08:40:00+00:00 | NEM | QLD1 | 0.0 | 66.08333333333333 | 0.0 | 56.7518165501313 | 0.0 | 0.0
2021-08-18 07:50:00+00:00 | NEM | VIC1 | 45.040255 | 60.8686625 | 4.323630091796656 | 49.19445586624939 | 0.0 | 0.0
2014-08-05 03:35:00+00:00 | NEM | QLD1 | 0.0 | 97.896745 | 0.0 | 81.72991630515779 | 0.0 | 0.0
```

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

Total rows: 11323595

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

```
interval | network_id | network_region | forecast_load | generation_scheduled | generation_non_scheduled | generation_total | price | is_forecast | net_interchange | demand_total | price_dispatch | net_interchange_trading | demand
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
2021-05-18 12:45:00 | NEM | VIC1 | None | None | None | None | None | False | -369.58 | 5398.7510 | 39.33064 | None | 5317.84
2012-12-16 14:40:00 | NEM | SA1 | None | None | None | None | None | False | 30.64 | 1229.17064 | 44.41999 | None | 1103.97
2015-12-17 06:45:00 | NEM | QLD1 | None | None | None | None | None | False | 335.52 | 6610.84375 | 54.5413 | None | 6321.2
2021-09-15 16:20:00 | NEM | QLD1 | None | None | None | None | None | False | 795.01 | 6204.9870 | 42.44382 | None | 6060.14
2012-01-28 02:40:00 | NEM | VIC1 | None | None | None | None | None | False | 1428.73 | 4923.497 | 16.18638 | None | 4836.23
```

## Table: bom_observation

Total rows: 5920234

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

```
observation_time | station_id | temp_apparent | temp_air | press_qnh | wind_dir | wind_spd | cloud | cloud_type | humidity | wind_gust | temp_max | temp_min
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
2021-03-18 03:30:00+00:00 | 066059 | 19.5 | 18.3 | None | E | 9 |  |  | 100 | 15 | None | None
2021-04-08 12:30:00+00:00 | 034035 | 21.2 | 21.1 | 1009.2 | NNE | 9 |  |  | 71 | 11 | None | None
2021-02-02 03:00:00+00:00 | 061366 | 19.2 | 22.0 | 1010.5 | S | 28 |  |  | 74 | 37 | None | None
1905-11-07 12:00:00+00:00 | 094029 | None | None | None | None | None | None | None | None | None | 19.4 | 9.2
2017-05-24 03:30:00+00:00 | 086338 | 11.7 | 14.3 | None | None | None | None | None | 11.6 | None | None | None
```

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

```
code | state | name | registered | geom | feed_url | is_capital | name_alias | priority | website_url | altitude | web_code
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
025562 | SA | AUSTIN PLAINS | None | 0101000020E6100000E17A14AE47916140713D0AD7A3B041C0 | http://www.bom.gov.au/fwo/IDS60801/IDS60801.94690.json | False | Lameroo AWS | 5 | http://www.bom.gov.au/products/IDS60801/IDS60801.94690.shtml | 110 | None
005007 | WA | LEARMONTH AIRPORT | None | 0101000020E61000006666666666865C403D0AD7A3703D36C0 | http://www.bom.gov.au/fwo/IDW60801/IDW60801.94302.json | False | Learmonth | 5 | http://www.bom.gov.au/products/IDW60801/IDW60801.94302.shtml | 5 | None
063077 | NSW | SPRINGWOOD (VALLEY HEIGHTS) | None | 0101000020E6100000C3F5285C8FD262407B14AE47E1DA40C0 | http://www.bom.gov.au/fwo/IDN60801/IDN60801.95744.json | False | Springwood | 5 | http://www.bom.gov.au/products/IDN60801/IDN60801.95744.shtml | 320 | None
015135 | NT | TENNANT CREEK AIRPORT | None | 0101000020E6100000F6285C8FC2C56040A4703D0AD7A333C0 | http://www.bom.gov.au/fwo/IDD60801/IDD60801.94238.json | False | Tennant Creek | 5 | http://www.bom.gov.au/products/IDD60801/IDD60801.94238.shtml | 375 | None
033210 | QLD | ST LAWRENCE | None | 0101000020E6100000713D0AD7A3B062409A999999995936C0 | http://www.bom.gov.au/fwo/IDQ60801/IDQ60801.95369.json | False | St Lawrence | 5 | http://www.bom.gov.au/products/IDQ60801/IDQ60801.95369.shtml | 9 | None
```

## Table: crawl_history

Total rows: 788264

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

```
source | crawler_name | network_id | interval | inserted_records | crawled_time | processed_time
---------------------------------------------------------------------------------------------------------
nemweb | au.nemweb.current.dispatch_is | NEM | 2024-02-15 23:30:00+00:00 | 16 | None | 2024-02-15 13:30:00+00:00
nemweb | au.nemweb.current.rooftop | NEM | 2023-10-29 01:00:00+00:00 | 5 | None | 2023-10-28 15:00:59+00:00
nemweb | au.nemweb.trading_is | NEM | 2023-03-20 23:05:00+00:00 | 5 | None | 2023-03-20 13:05:07+00:00
nemweb | au.nemweb.trading_is | NEM | 2022-09-06 18:15:00+00:00 | 5 | None | 2022-09-06 08:15:57+00:00
nemweb | au.nemweb.dispatch_scada | NEM | 2023-05-09 04:50:00+00:00 | 430 | None | 2023-05-08 18:50:02+00:00
```

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

```
spider_name | data | created_at | updated_at
------------------------------------------------------------
au.mms.trading_regionsum | {'version': '2', 'last_crawled': '2022-10-25T08:04:19+11:00'} | 2022-10-24 21:04:20.104853+00:00 | 2022-10-24 21:04:20.333853+00:00
au.nemweb.archive.trading_is | {'version': '2', 'last_crawled': '2024-09-04T09:46:26+10:00'} | 2022-07-21 01:09:02.568398+00:00 | 2024-09-03 23:46:26.177996+00:00
au.nem.latest.dispatch_is | {'version': '2', 'last_crawled': '2022-06-23T12:37:43+10:00', 'server_latest': '2022-06-23T12:45:00+10:00', 'latest_processed': '2022-06-23T12:45:00+10:00'} | 2022-06-18 11:10:03.273082+00:00 | 2022-06-23 02:44:26.760678+00:00
au.nem.archive.dispatch_scada | {'version': '2', 'last_crawled': '2022-06-10T17:58:07+10:00'} | 2022-06-10 07:58:07.656878+00:00 | 2022-06-10 07:58:07.677975+00:00
apvi.today.data | {'version': '2', 'last_crawled': '2023-09-29T10:55:51+10:00', 'server_latest': '2023-09-29T10:30:00+10:00', 'latest_processed': '2023-09-29T10:30:00+10:00'} | 2022-06-10 05:54:16.106149+00:00 | 2023-09-29 00:55:52.800735+00:00
```

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

```
created_by | created_at | updated_at | id | network_id | fueltech_id | status_id | station_id | code | network_code | network_region | network_name | active | dispatch_type | capacity_registered | registered | deregistered | unit_id | unit_number | unit_alias | unit_capacity | approved | approved_by | approved_at | emissions_factor_co2 | interconnector | interconnector_region_to | data_first_seen | data_last_seen | expected_closure_date | expected_closure_year | interconnector_region_from | emission_factor_source | include_in_geojson
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
opennem.registry | 2020-12-09 15:34:57.152482+00:00 | 2024-06-07 13:12:37.960819+00:00 | 567 | WEM | distillate | operating | 408 | TESLA_PICTON_G1 | WEM | WEM | None | True | GENERATOR | 9.9 | 2011-07-27 00:00:00 | None | None | None | None | None | True | None | 2020-12-09 15:34:57.152459+00:00 | 0.97 | False | None | 2014-03-07 06:30:00+00:00 | 2024-08-01 23:55:00+00:00 | None | None | None | None | True
opennem.registry | 2020-12-09 15:33:49.491388+00:00 | 2024-06-07 13:11:43.311134+00:00 | 238 | NEM | coal_black | operating | 171 | KPP_1 | NEM | QLD1 | None | True | GENERATOR | 744.0 | None | None | None | None | None | None | True | None | 2020-12-09 15:33:49.491375+00:00 | 0.83104 | False | None | 2007-05-12 07:30:00+00:00 | 2024-08-03 00:50:00+00:00 | None | None | None | None | True
opennem.registry | 2020-12-09 15:33:18.767542+00:00 | 2024-06-07 13:12:05.670696+00:00 | 65 | NEM | gas_steam | retired | 46 | BELLBAY2 | NEM | TAS1 | None | True | GENERATOR | 120.0 | None | None | None | None | None | None | True | None | 2020-12-09 15:33:18.767529+00:00 | 0.70856 | False | None | 2005-05-16 03:35:00+00:00 | 2009-03-31 20:00:00+00:00 | None | None | None | None | True
opennem.registry | 2020-12-09 15:33:42.283065+00:00 | 2023-03-31 04:51:13.576551+00:00 | 192 | NEM | solar_utility | operating | 142 | HAMISF1 | NEM | QLD1 | None | True | GENERATOR | 57.0 | None | None | None | None | None | None | True | None | 2020-12-09 15:33:42.283052+00:00 | 0.0 | False | None | 2018-07-10 02:40:00+00:00 | 2024-08-03 00:50:00+00:00 | None | None | None | None | True
opennem.init | 2021-04-13 13:47:33.279399+00:00 | 2023-03-31 04:51:05.874238+00:00 | 675 | NEM | hydro | retired | 483 | SNOWY4 | None | NSW1 | None | True | GENERATOR | None | None | None | None | None | None | None | True | None | None | 0.0 | False | None | 1998-12-06 17:15:00+00:00 | 2001-03-26 06:55:00+00:00 | None | None | None | None | True
```

## Table: facility_scada

Total rows: 769210786

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

```
network_id | interval | facility_code | generated | eoi_quantity | is_forecast | energy_quality_flag | energy
------------------------------------------------------------------------------------------------------------------------
NEM | 2008-09-03 08:20:00 | URANQ12 | 0.0 | None | False | 1 | 0E-20
NEM | 2022-09-19 07:40:00 | BANN1 | 34.25 | None | False | 0 | 2.6970833333333333
NEM | 2017-07-05 00:25:00 | TUNGATIN | 0.0 | 0.0 | False | 1 | 0E-20
NEM | 2023-05-27 05:00:00 | GERMCRK | 6.1 | None | False | 0 | 0.51250000000000000000
NEM | 2018-04-11 17:10:00 | HUMENSW | 28.11691 | None | False | 1 | 2.3199754166666667
```

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

```
code | label
------------------------------
permitted | Permitted
maturing | Maturing
construction | Construction
commissioning | Commissioning
emerging | Emerging
```

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

### Sample Data

```
id | subject | description | email | twitter | user_ip | user_agent | created_at | alert_sent
---------------------------------------------------------------------------------------------------------------------------------------
16 | Ballarat facility feedback | 
**Path:**
/facility/au/NEM/BALBESS/?range=7d&interval=30m

**Sources:**
test

**Fields:**

```
[
 {
  "key": "Facility status and dates",
  "value": "operating since  6 Nov 2018"
 }
]
```

**Descript... | steven@test.com | None | 61.68.241.134 | Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 | 2021-07-03 04:10:30.255253+00:00 | True
32 | Bango facility feedback | 
**No email provided.**
   

**Path:**
/facility/au/NEM/BANGOWF/?range=7d&interval=30m

**Sources:**
sdf

**Fields:**

```
[]
```

**Description:**
sdf
 | None | None | 61.68.241.134 | Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 | 2021-07-03 05:55:14.915077+00:00 | True
68 | Bayswater facility feedback | 
**Email:**
jcocks64@gmail.com     
   

**Path:**
/facility/au/NEM/BAYSW/?range=3d&interval=30m

**Sources:**
https://www.wikiwand.com/en/Bayswater_Power_Station

**Fields:**

```
[
 {
  "key": "Faci... | jcocks64@gmail.com | None | 172.19.0.1 | Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 | 2023-09-19 11:49:37.992583+00:00 | False
78 | Callide B facility feedback | 
**Email:**
mushalik@tpg.com.au     
   

**Path:**
/facility/au/NEM/CALL_B/?range=3d&interval=30m

**Sources:**
https://opennem.org.au/facility/au

**Fields:**

```
[]
```

**Description:**
No more d... | mushalik@tpg.com.au | None | 172.19.0.1 | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 | 2023-12-14 02:19:05.833648+00:00 | False
33 | Bango facility feedback | 
**No email provided.**
   

**Path:**
/facility/au/NEM/BANGOWF/?range=7d&interval=30m

**Sources:**
test

**Fields:**

```
[
 {
  "key": "BANGOWF1 label",
  "value": "BANGOWF1"
 }
]
```

**Descriptio... | None | None | 61.68.241.134 | Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 | 2021-07-03 06:00:12.114265+00:00 | True
```

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

```
created_by | created_at | updated_at | code | label | renewable | fueltech_group_id
---------------------------------------------------------------------------------------------------------
None | 2020-12-09 01:46:29.027817+00:00 | 2022-10-04 06:24:38.567367+00:00 | battery_discharging | Battery (Discharging) | True | battery_discharging
None | 2020-12-09 01:46:29.318789+00:00 | 2022-10-04 06:24:38.815381+00:00 | distillate | Distillate | False | distillate
None | 2020-12-09 01:46:29.904852+00:00 | 2022-10-04 06:24:39.329845+00:00 | solar_rooftop | Solar (Rooftop) | True | solar
None | 2020-12-09 01:46:29.087850+00:00 | 2024-08-10 04:20:43.258203+00:00 | bioenergy_biogas | Biogas | False | bioenergy
None | 2024-08-10 04:20:45.089031+00:00 | None | battery | Battery | True | None
```

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

```
created_by | created_at | updated_at | code | label | color | renewable
---------------------------------------------------------------------------------------------------------
None | 2022-10-04 06:24:38.461796+00:00 | 2024-08-13 02:51:57.973473+00:00 | pumps | Pumps | #88AFD0 | True
None | 2022-10-04 06:24:38.214596+00:00 | 2024-08-13 02:51:57.574303+00:00 | battery_charging | Battery (Charging) | #B2DAEF | True
None | 2022-10-04 06:24:38.054393+00:00 | None | gas | Gas | #FF8813 | False
None | 2022-10-04 06:24:38.163568+00:00 | 2024-08-13 02:51:57.473752+00:00 | solar | Solar | #FED500 | True
None | 2022-10-04 06:24:38.411012+00:00 | None | bioenergy | Bioenergy | #A3886F | False
```

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

```
f_table_catalog | f_table_schema | f_table_name | f_geometry_column | coord_dimension | srid | type
---------------------------------------------------------------------------------------------------------
opennem | public | location | boundary | 2 | 4326 | POLYGON
opennem | public | location | geom | 2 | 4326 | POINT
opennem | public | bom_station | geom | 2 | 4326 | POINT
```

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

```
id | address1 | address2 | locality | state | postcode | place_id | geocode_approved | geocode_skip | geocode_processed_at | geocode_by | geom | osm_way_id | boundary
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
13581 |  |  |  | QLD | None | None | True | False | None | opennem.registry | 0101000020E6100000F27B55D675326240F021E37236C431C0 | None | None
13567 |  |  |  | SA | None | None | True | False | None | opennem.registry | 0101000020E610000027DE019E34516140C8D2872EA88740C0 | None | None
13515 |  |  |  | QLD | None | None | True | False | None | opennem.registry | 0101000020E6100000DD09DB2F29DE6240800C4D6317163BC0 | None | None
4868 | None | None |  | None | None | None | False | False | None | None | None | None | None
13805 | None | None | None | NSW | None | None | False | False | None | None | None | None | None
```

## Table: milestones

Total rows: 15123

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

```
instance_id | record_id | interval | significance | value | network_id | fueltech_id | description | period | aggregate | metric | value_unit | description_long | network_region | previous_instance_id
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
1e980fc9-78e5-4c7b-8e74-1b41c1317dde | au.nem.vic1.battery_charging.energy.day.high | 2021-11-12 00:00:00 | 9 | 798.3735 | NEM | battery_charging | Daily battery (charging) energy high record for NEM in Victoria | day | high | energy | MWh | None | VIC1 | 1aafdf14-e70a-4872-b1ee-12224e787133
832ddc60-d124-4849-b458-029c6b7a3ac8 | au.nem.qld1.coal.emissions.month.high | 2017-07-01 00:00:00 | 8 | 4287139.3535 | NEM | coal | Monthly coal emissions high record for NEM in Queensland | month | high | emissions | tCO2e | None | QLD1 | 0600ca5c-63dd-4928-bbde-f0d6d89be65e
c43614bb-68ad-4120-8b0f-3740ea3f2248 | au.nem.demand.interval.low | 2005-04-06 00:00:00 | 4 | 1195.02 | NEM | demand | Interval demand low record for NEM | interval | low | demand | MW | None | None | 72d35d5f-b485-4a5d-b727-9e93510f4628
0d97cade-355d-4978-a580-f95098224c35 | au.nem.vic1.gas.power.interval.high | 2000-01-13 16:00:00 | 4 | 989.15 | NEM | gas | Interval gas power high record for NEM in Victoria | interval | high | power | MW | None | VIC1 | a4114eb6-df81-4f68-9cfd-1ca292806719
135983df-37a7-47e6-a855-cfa4d2da7444 | au.wem.bioenergy.energy.month.low | 2015-06-01 00:00:00 | 8 | 10046.7955 | WEM | bioenergy | Monthly bioenergy energy low record for WEM | month | low | energy | MWh | None | None | None
```

## Table: mv_fueltech_daily

Total rows: 361037

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

```
trading_day | network_id | network_region | fueltech_code | generated | energy | emissions | emissions_intensity
------------------------------------------------------------------------------------------------------------------------
2005-12-08 00:00:00 | NEM | NSW1 | hydro | 205885.3400 | 17160.5529 | 0.0000 | 0.0000
2018-09-05 00:00:00 | AEMO_ROOFTOP | SA1 | solar_rooftop | 5268.0980 | 2634.0490 | None | None
2008-10-24 00:00:00 | NEM | QLD1 | coal_black | 1714506.5799 | 142869.2897 | 136715.6232 | 0.9569
2019-05-22 00:00:00 | APVI | SA1 | solar_rooftop | 13574.1303 | 3393.5326 | None | None
2013-02-15 00:00:00 | WEM | WEM | wind | None | None | 0 | 0
```

## Table: mv_weather_observations

Total rows: 5409699

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

```
observation_time | station_id | temp_air | temp_min | temp_max
---------------------------------------------------------------------------
2020-12-28 10:30:00+00:00 | 040043 | 24.2000000000000000 | 24.2 | 24.2
2021-03-30 05:00:00+00:00 | 080091 | 23.6000000000000000 | 23.6 | 23.6
2009-02-12 16:00:00+00:00 | 066214 | 20.0000000000000000 | 20.0 | 20.0
2012-05-08 01:00:00+00:00 | 040913 | 13.9000000000000000 | 13.9 | 13.9
2020-12-17 15:30:00+00:00 | 028008 | 24.9000000000000000 | 24.9 | 24.9
```

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

```
created_by | created_at | updated_at | code | country | label | timezone | interval_size | offset | timezone_database | export_set | interval_shift | network_price | data_start_date | data_end_date
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
None | 2021-04-12 07:06:18.835747+00:00 | 2024-08-10 04:32:14.674557+00:00 | AEMO_ROOFTOP_BACKFILL | au | AEMO Rooftop Backfill | Australia/Brisbane | 30 | 600 | AEST | False | 0 | NEM | None | None
None | 2021-04-09 10:15:56.408641+00:00 | 2024-08-10 04:32:14.576316+00:00 | AEMO_ROOFTOP | au | AEMO Rooftop | Australia/Brisbane | 30 | 600 | AEST | False | 0 | NEM | 2016-07-31 14:30:00+00:00 | 2024-08-02 23:30:00+00:00
None | 2024-08-10 04:32:14.380672+00:00 | None | WEMDE | au | WEMDE | Australia/Perth | 5 | 480 | AWST | True | 0 | WEMDE | None | None
None | 2023-02-22 09:54:49.679305+00:00 | 2024-08-10 04:32:14.781558+00:00 | OPENNEM_ROOFTOP_BACKFILL | au | OpenNEM Rooftop Backfill | Australia/Brisbane | 30 | 600 | AEST | False | 0 | NEM | 2015-03-19 20:15:00+00:00 | 2018-02-28 09:30:00+00:00
None | 2020-12-09 01:46:31.057929+00:00 | 2024-08-10 04:32:14.138129+00:00 | NEM | au | NEM | Australia/Brisbane | 5 | 600 | AEST | True | 5 | NEM | 1998-12-06 15:40:00+00:00 | 2024-08-03 00:15:00+00:00
```

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

```
created_by | created_at | updated_at | network_id | code | timezone | timezone_database | offset | export_set
---------------------------------------------------------------------------------------------------------------------------------------
None | 2021-04-09 10:15:56.438248+00:00 | None | AEMO_ROOFTOP | QLD1 | None | None | None | True
None | 2021-04-09 10:15:56.441786+00:00 | None | AEMO_ROOFTOP | VIC1 | None | None | None | True
None | 2020-12-09 01:46:31.422815+00:00 | None | NEM | VIC1 | None | None | None | True
None | 2021-04-09 10:15:56.445329+00:00 | None | AEMO_ROOFTOP | TAS1 | None | None | None | True
None | 2020-12-09 01:46:31.363840+00:00 | None | NEM | QLD1 | None | None | None | True
```

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

```
participantid | participantclassid | name | id | description | code | acn | primarybusiness | name | lastchanged | network_name | network_code | country | abn | approved | approved_by | approved_at
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
53 | ERMPOWER | ERMPowerRetailPty | None | None | None | None | False | None | None
84 | WATERCP | WaterCorporation | None | None | None | None | False | None | None
155 | Neoenaus | NeoenAustralia | None | None | None | None | False | None | None
168 | Sfmoora | SolarFarmMooraPty | None | None | None | None | False | None | None
187 | Vivapwr | VivoPowerWAPty.. | None | None | None | None | False | None | None
```

## Table: pg_stat_statements

Total rows: 100

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

```
userid | dbid | toplevel | queryid | query | plans | total_plan_time | min_plan_time | max_plan_time | mean_plan_time | stddev_plan_time | calls | total_exec_time | min_exec_time | max_exec_time | mean_exec_time | stddev_exec_time | rows | shared_blks_hit | shared_blks_read | shared_blks_dirtied | shared_blks_written | local_blks_hit | local_blks_read | local_blks_dirtied | local_blks_written | temp_blks_read | temp_blks_written | blk_read_time | blk_write_time | wal_records | wal_fpi | wal_bytes
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
16384 | 16448 | True | 6960685409981736324 | SELECT column_name FROM information_schema.columns WHERE table_name = $1 ORDER BY ordinal_position | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 25 | 8.830414 | 0.081189 | 2.8804469999999998 | 0.35321655999999996 | 0.6128130249196785 | 240 | 4188 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.0 | 0 | 0 | 0
16384 | 16448 | True | -2238260910044563148 | SELECT
            $1 || relname || $2 ||
            array_to_string(
                array_agg(
                    $3 || column_name || $4 ||  type || $5|| not_null
                )
              ... | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 29 | 11.433968999999998 | 0.046990000000000004 | 9.286489999999999 | 0.3942747931034482 | 1.6806096805062956 | 29 | 939 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.0 | 0 | 0 | 0
16384 | 16448 | True | 3749380189022910195 | ROLLBACK | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 62 | 0.07687499999999999 | 0.00027 | 0.01974 | 0.0012399193548387093 | 0.002456070795307186 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.0 | 0 | 0 | 0
16384 | 16448 | True | 4629810609182828207 | RESET ALL | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 3 | 0.02708 | 0.00834 | 0.00954 | 0.009026666666666667 | 0.0005049972497174833 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.0 | 0 | 0 | 0
16384 | 16448 | True | 6722864136054051285 | SELECT COUNT(*) FROM fueltech_group | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 0.478673 | 0.478673 | 0.478673 | 0.478673 | 0.0 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.0 | 0 | 0 | 0
```

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

```
dealloc | stats_reset
------------------------------
0 | 2024-09-09 22:19:07.454676+00:00
```

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

Total rows: 8500

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

```
srid | auth_name | auth_srid | srtext | proj4text
---------------------------------------------------------------------------
5358 | EPSG | 5358 | GEOCCS["SIRGAS-Chile",DATUM["SIRGAS_Chile",SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],AUTHORITY["EPSG","1064"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["metre",1,A... | +proj=geocent +ellps=GRS80 +units=m +no_defs 
4724 | EPSG | 4724 | GEOGCS["Diego Garcia 1969",DATUM["Diego_Garcia_1969",SPHEROID["International 1924",6378388,297,AUTHORITY["EPSG","7022"]],TOWGS84[208,-435,-229,0,0,0,0],AUTHORITY["EPSG","6724"]],PRIMEM["Greenwich",0,A... | +proj=longlat +ellps=intl +towgs84=208,-435,-229,0,0,0,0 +no_defs 
3363 | EPSG | 3363 | PROJCS["NAD83(HARN) / Pennsylvania North (ftUS)",GEOGCS["NAD83(HARN)",DATUM["NAD83_High_Accuracy_Reference_Network",SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],TOWGS84[0,0,0,0,... | +proj=lcc +lat_1=41.95 +lat_2=40.88333333333333 +lat_0=40.16666666666666 +lon_0=-77.75 +x_0=600000 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=us-ft +no_defs 
2687 | EPSG | 2687 | PROJCS["Pulkovo 1995 / 3-degree Gauss-Kruger zone 53",GEOGCS["Pulkovo 1995",DATUM["Pulkovo_1995",SPHEROID["Krassowsky 1940",6378245,298.3,AUTHORITY["EPSG","7024"]],TOWGS84[24.47,-130.89,-81.56,0,0,0.1... | +proj=tmerc +lat_0=0 +lon_0=159 +k=1 +x_0=53500000 +y_0=0 +ellps=krass +towgs84=24.47,-130.89,-81.56,0,0,0.13,-0.22 +units=m +no_defs 
104702 | ESRI | 104702 | GEOGCS["GCS_NAD_1983_HARN_Adj_MN_Beltrami_North",DATUM["D_NAD_1983_HARN_Adj_MN_Beltrami_North",SPHEROID["S_GRS_1980_Adj_MN_Beltrami_North",6378505.809,298.257222100883,AUTHORITY["ESRI","107702"]],AUTH... | +proj=longlat +a=6378505.809 +rf=298.257222100883 +no_defs
```

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

```
created_by | stationid | created_at | stationname | address1 | updated_at | address2 | id | address3 | participant_id | address4 | location_id | code | city | state | name | description | postcode | lastchanged | wikipedia_link | connectionpointid | wikidata_id | network_code | network_name | approved | approved_by | approved_at | website_url
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
opennem.registry | 2020-12-09 15:32:39.826093+00:00 | 2024-06-07 13:11:45.449251+00:00 | 231 | None | 13646 | OAKEY | Oakey | The Oakey Power Station is a 332 MW power station located at Oakey on the Darling Downs in southern Queensland, adjacent to the Roma to Brisbane Pipeline. The station is an open-cycle, dual liquid/gas... | https://en.wikipedia.org/wiki/Oakey_Power_Station | Q7073856 | None | Oakey | True | opennem.importer.facilities | 2024-06-07 23:11:45.518754+00:00 | None
opennem.registry | 2020-12-09 15:32:39.826093+00:00 | 2024-06-07 13:11:13.702014+00:00 | 33 | None | 13448 | BANKSPT | Bankstown Sports Club | None | None | None | None | Bankstown Sports Club | True | opennem.importer.facilities | 2024-06-07 23:11:13.747542+00:00 | None
opennem.registry | 2020-12-09 15:32:39.826093+00:00 | 2024-06-07 13:11:53.893632+00:00 | 53 | None | 13468 | BNGSF1 | Bungala One | None | None | None | None | Bungala One | True | opennem.importer.facilities | 2024-06-07 23:11:53.937745+00:00 | None
opennem.registry | 2020-12-09 15:32:39.826093+00:00 | 2024-06-07 13:11:25.202836+00:00 | 209 | None | 13624 | MM | Munmorah | Munmorah Power Station is a demolished coal fired electricity power station with four 350 MW English Electric steam driven turbo-alternators for a combined capacity of 1,400 MW. The station was locate... | https://en.wikipedia.org/wiki/Munmorah_Power_Station | Q11990196 | None | Munmorah | True | opennem.importer.facilities | 2024-06-07 23:11:25.283456+00:00 | None
opennem.importer.facilities | 2023-04-26 23:10:22.910976+00:00 | 2024-06-07 13:12:40.796131+00:00 | 544 | None | 13838 | PIBESS | Phillip Island BESS | None | None | None | None | Phillip Island BESS | True | opennem.importer.facilities | 2024-06-07 23:12:40.843242+00:00 | https://mondo.com.au/projects/phillip-island-battery
```

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

```
created_by | created_at | updated_at | stat_date | country | stat_type | value
---------------------------------------------------------------------------------------------------------
None | 2021-01-05 09:47:54.294658+00:00 | None | 2008-06-30 00:00:00+00:00 | au | CPI | 91.6
None | 2021-01-05 09:47:54.294658+00:00 | None | 1958-09-01 00:00:00+00:00 | au | CPI | 7.2
None | 2021-01-05 09:47:54.294658+00:00 | None | 1978-09-30 00:00:00+00:00 | au | CPI | 22.1
None | 2021-01-05 09:47:54.294658+00:00 | None | 2020-09-30 00:00:00+00:00 | au | CPI | 116.2
None | 2021-01-05 09:47:54.294658+00:00 | None | 1953-12-01 00:00:00+00:00 | au | CPI | 6.4
```

## Table: task_profile

Total rows: 568157

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

```
id | task_name | time_start | time_end | time_sql | time_cpu | errors | retention_period | level | invokee_name
------------------------------------------------------------------------------------------------------------------------------------------------------
fea18795-18f7-4705-8c7c-79c74282a647 | wem_per_interval_check | 2024-07-03 12:48:13.130418+00:00 | 2024-07-03 12:48:25.812759+00:00 | None | None | 0 | forever | noisy | 
e700bd6c-8c2d-4d14-a6a3-5cc8d6996a4c | wem_per_interval_check | 2024-03-03 16:22:32.441213+00:00 | 2024-03-03 16:22:50.829095+00:00 | None | None | 0 | forever | noisy | 
9d54d80a-98d1-4604-8424-b84b194aced1 | run_aggregate_flow_for_interval_v3 | 2024-07-18 03:40:00.540690+00:00 | 2024-07-18 03:40:00.647996+00:00 | None | None | 0 | forever | info | 
f07db03c-d7a1-4830-af1f-0081ef7bcd81 | run_aggregate_flow_for_interval_v3 | 2024-07-03 16:20:00.686086+00:00 | 2024-07-03 16:20:00.760331+00:00 | None | None | 0 | forever | info | 
f9fc00ac-9d07-4adb-bb07-dcf24cccc0ce | nem_dispatch_scada_crawl | 2024-02-14 13:30:59.285936+00:00 | 2024-02-14 13:34:18.366702+00:00 | None | None | 0 | forever | noisy | 
```
