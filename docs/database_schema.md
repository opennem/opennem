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

| notice_id | notice_type | creation_date | issue_date | external_reference | reason |
| --- | --- | --- | --- | --- | --- |
| 118053 | RECLASSIFY CONTINGENCY | 2024-09-02 10:04:07 | 2024-09-02 00:00:00 | Cancellation of a Non-Credible Contingency Event: Farrell-John Butters line and Farrell-Rosebery-Newton-Queenstown line in TAS1 due to Lightning. | Cancellation of reclassification of a Non-Credible Contingency Event as a Credible Contingency Event due to Lightning. AEMO considers the simultaneous trip of the following circuits is no longer reaso... |
| 117699 | MARKET INTERVENTION | 2024-08-16 15:28:53 | 2024-08-16 00:00:00 | Cancellation: Direction issued to:  AGL SA Generation Pty Limited - TORRB3 TORRENS ISLAN | AEMO ELECTRICITY MARKET NOTICE

Cancellation: Direction issued to:  AGL SA Generation Pty Limited - TORRB3 TORRENS ISLAN

Refer to Market Notice 117681

Direction is cancelled from: 1530 hrs 16/08/202... |
| 117997 | RECLASSIFY CONTINGENCY | 2024-08-31 01:41:27 | 2024-08-31 00:00:00 | Reclassification of a Non-Credible Contingency Event: Lindisfarne - Mornington No.1 TEE line and Lindisfarne - Mornington No.2 TEE line in TAS1 due to Lightning. | Reclassification of a Non-Credible Contingency Event as a Credible Contingency Event due to Lightning. AEMO considers the simultaneous trip of the following circuits to now be more likely and reasonab... |
| 117972 | PRICES UNCHANGED | 2024-08-29 19:35:40 | 2024-08-29 00:00:00 | [EventId:202408291920_confirmed] Prices for interval 29-Aug-2024 19:20 are now confirmed | AEMO ELECTRICITY MARKET NOTICE

Issued by Australian Energy Market Operator Ltd at 1930 hrs on 29 August 2024

PRICES ARE NOW CONFIRMED for trading interval 29-Aug-2024 19:20.

In accordance with Mark... |
| 117712 | MARKET INTERVENTION | 2024-08-18 16:17:21 | 2024-08-18 00:00:00 | Direction - SA region 18/08/2024 | AEMO ELECTRICITY MARKET NOTICE

Direction - SA region 18/08/2024

Refer to Market Notice 117711

In accordance with section 116 of the National Electricity Law, AEMO is issuing a direction to AGL SA G... |

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

| version_num |
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

| keyid | description | revoked | created_at |
| --- | --- | --- | --- |
| DQwfwdHCzjBmnM5yMgkAVg | opennem default | False | 2021-05-27 12:28:38.314071+00:00 |

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

| trading_day | network_id | facility_code | fueltech_id | energy | market_value | emissions | network_region |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-04-07 00:00:00+00:00 | NEM | PPCCGT | gas_ccgt | 8172.56245166666651 | 756200.3061302066037517222 | 3871.404127572887425785825 | SA1 |
| 2016-03-11 00:00:00+00:00 | NEM | BARRON-1 | hydro | 364.8583333333333424 | 18619.50959703333365270545 | 0E-17 | QLD1 |
| 2008-03-14 00:00:00+00:00 | WEM | WEST_KALGOORLIE_GT2 | distillate | 0 | 0 | 0 | WEM |
| 2022-10-14 00:00:00+00:00 | NEM | WHITSF1 | solar_utility | 512.0416666666666636 | 27644.227848958332669767614 | 0E-17 | QLD1 |
| 2023-08-01 00:00:00+00:00 | NEM | GLRWNSF1 | solar_utility | 318.715833333333339074 | 23275.3844791666670372248450000000000042 | 0E-19 | VIC1 |

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

| trading_day | network_id | network_region | demand_energy | demand_market_value |
| --- | --- | --- | --- | --- |
| 2014-05-19 00:00:00+00:00 | NEM | TAS1 | 30.63305084666666666668 | 1051973.2597649294416672877448000 |
| 2002-03-03 00:00:00+00:00 | NEM | NSW1 | 27.93518166666666666668 | 604258.8421500000000001394000 |
| 2008-08-27 00:00:00+00:00 | NEM | NSW1 | 236.26295166666666666669 | 1595005.7818166666666654662000 |
| 2003-04-11 00:00:00+00:00 | NEM | NSW1 | 32.33671333333333333332 | 539351.9580083333333331225000 |
| 2012-09-10 00:00:00+00:00 | WEM | WEM | None | None |

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

| trading_interval | network_id | network_region | energy_imports | energy_exports | emissions_imports | emissions_exports | market_value_imports | market_value_exports |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014-06-26 17:40:00+00:00 | NEM | NSW1 | 152.043205 | 0.0 | 145.0811012847138 | 0.0 | 0.0 | 0.0 |
| 2021-07-27 05:20:00+00:00 | NEM | QLD1 | 0.0 | 77.022465 | 0.0 | 56.18997644940283 | 0.0 | 0.0 |
| 2011-02-02 12:15:00+00:00 | NEM | SA1 | 21.75 | 0.0 | 25.678122202753123 | 0.0 | 0.0 | 0.0 |
| 2009-07-17 18:35:00+00:00 | NEM | NSW1 | 109.58333333333334 | 0.0 | 125.20888235820357 | 0.0 | 0.0 | 0.0 |
| 2020-03-17 16:55:00+00:00 | NEM | VIC1 | 15.66101 | 103.40275583333333 | 2.5273120583425808 | 92.34664486121406 | 0.0 | 0.0 |

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

Total rows: 11,323,605

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

| interval | network_id | network_region | forecast_load | generation_scheduled | generation_non_scheduled | generation_total | price | is_forecast | net_interchange | demand_total | price_dispatch | net_interchange_trading | demand |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2021-11-30 04:05:00 | NEM | NSW1 | None | None | None | None | 59.72 | False | -513.19 | 6293.8056 | 59.7199 | None | 6278.79 |
| 2011-12-03 05:55:00 | NEM | TAS1 | None | None | None | None | None | False | -228.63 | 1115.73157 | 12.08 | None | 993.91 |
| 2020-01-20 15:00:00 | NEM | TAS1 | None | None | None | None | 29.87 | False | -445 | 1170.825260 | 89.08707 | -438.37 | 1099.23 |
| 2021-06-17 01:00:00 | NEM | VIC1 | None | None | None | None | 106.4 | False | -146.83 | 4983.4030 | 97.05558 | -106.77 | 4931.24 |
| 2015-12-20 17:45:00 | NEM | NSW1 | None | None | None | None | None | False | -1351.84 | 10937.36296 | 46.0553 | None | 10780.37 |

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

| observation_time | station_id | temp_apparent | temp_air | press_qnh | wind_dir | wind_spd | cloud | cloud_type | humidity | wind_gust | temp_max | temp_min |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2021-04-07 23:00:00+00:00 | 068253 | None | 20.5 | 1013.8 | SW | 4 |  |  | None | 7 | None | None |
| 2021-04-03 07:50:00+00:00 | 250042 | 26.2 | 25.5 | None | CALM | 0 |  |  | 43 | 2 | None | None |
| 2021-02-02 22:00:00+00:00 | 084016 | 10.1 | 18.1 | 1013.6 | SSW | 46 | Mostly cloudy |  | 69 | 54 | None | None |
| 2021-03-07 11:00:00+00:00 | 088166 | 17.2 | 20.0 | None | SSW | 6 |  |  | 30 | 7 | None | None |
| 2021-04-20 22:00:00+00:00 | 009542 | 9.6 | 11.0 | 1023.5 | NNW | 9 | Partly cloudy |  | 99 | 11 | None | None |

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

| code | state | name | registered | geom | feed_url | is_capital | name_alias | priority | website_url | altitude | web_code |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 061055 | NSW | NEWCASTLE NOBBYS SIGNAL STATION AWS | None | 0101000020E61000009A99999999F96240F6285C8FC27540C0 | http://www.bom.gov.au/fwo/IDN60801/IDN60801.94774.json | False | Newcastle Nobbys | 5 | http://www.bom.gov.au/products/IDN60801/IDN60801.94774.shtml | 33 | None |
| 024584 | SA | PALLAMANA AERODROME | None | 0101000020E61000008FC2F5285C67614048E17A14AE8741C0 | http://www.bom.gov.au/fwo/IDS60801/IDS60801.95818.json | False | Pallamana | 5 | http://www.bom.gov.au/products/IDS60801/IDS60801.95818.shtml | 45 | None |
| 014299 | NT | NGUKURR AIRPORT | None | 0101000020E61000000000000000D86040713D0AD7A3702DC0 | http://www.bom.gov.au/fwo/IDD60801/IDD60801.94106.json | False | Ngukurr AWS | 5 | http://www.bom.gov.au/products/IDD60801/IDD60801.94106.shtml | 14 | None |
| 031209 | QLD | COOKTOWN AIRPORT | None | 0101000020E6100000AE47E17A142662406666666666E62EC0 | http://www.bom.gov.au/fwo/IDQ60801/IDQ60801.95283.json | False | Cooktown | 5 | http://www.bom.gov.au/products/IDQ60801/IDQ60801.95283.shtml | 4 | None |
| 068241 | NSW | SHELLHARBOUR AIRPORT | None | 0101000020E6100000E17A14AE47D9624048E17A14AE4741C0 | http://www.bom.gov.au/fwo/IDN60801/IDN60801.95748.json | False | Albion Park | 5 | http://www.bom.gov.au/products/IDN60801/IDN60801.95748.shtml | 8 | None |

## Table: crawl_history

Total rows: 788,270

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

| source | crawler_name | network_id | interval | inserted_records | crawled_time | processed_time |
| --- | --- | --- | --- | --- | --- | --- |
| nemweb | au.nemweb.rooftop_forecast | NEM | 2022-11-01 22:30:00+00:00 | 1735 | None | 2022-11-01 12:33:43+00:00 |
| nemweb | au.nemweb.trading_is | NEM | 2023-05-19 07:15:00+00:00 | 5 | None | 2023-05-18 21:15:03+00:00 |
| nemweb | au.nemweb.current.trading_is | NEM | 2024-01-06 14:40:00+00:00 | 5 | None | 2024-01-15 14:50:05+00:00 |
| nemweb | au.nemweb.current.dispatch_scada | NEM | 2023-11-16 13:05:00+00:00 | 447 | None | 2023-11-16 03:05:58+00:00 |
| nemweb | au.nemweb.dispatch_is | NEM | 2023-07-22 10:30:00+00:00 | 16 | None | 2023-07-22 00:30:01+00:00 |

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

| spider_name | data | created_at | updated_at |
| --- | --- | --- | --- |
| au.mms.trading_is | {'version': '2', 'last_crawled': '2022-10-10T11:04:11+11:00'} | 2022-10-10 00:04:11.912748+00:00 | 2022-10-10 00:04:19.476002+00:00 |
| au.webde.history.facility_scada | {'last_crawled': '2024-08-03T10:53:32+10:00', 'server_latest': '2024-08-01T00:00:00', 'latest_interval': '2024-08-02T07:55:00+08:00', 'latest_processed': '2024-01-15T11:46:14+11:00'} | 2024-01-14 20:47:59.503046+00:00 | 2024-08-03 00:53:32.027994+00:00 |
| au.nemweb.archive.trading_is | {'version': '2', 'last_crawled': '2024-09-04T09:46:26+10:00'} | 2022-07-21 01:09:02.568398+00:00 | 2024-09-03 23:46:26.177996+00:00 |
| au.nem.latest.trading_is | {'version': '2', 'last_crawled': '2022-08-09T12:09:40+10:00', 'server_latest': '2022-06-12T12:40:00+10:00', 'latest_processed': '2022-06-12T12:40:00+10:00'} | 2022-06-10 06:30:16.615219+00:00 | 2022-08-09 02:09:40.520037+00:00 |
| au.nemweb.current.rooftop | {'version': '2', 'last_crawled': '2024-09-03T16:30:48+10:00', 'server_latest': '2024-08-03T10:00:00+10:00', 'latest_processed': '2024-08-03T10:00:00+10:00'} | 2023-09-04 10:13:46.256873+00:00 | 2024-09-03 06:30:48.694505+00:00 |

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

| created_by | created_at | updated_at | id | network_id | fueltech_id | status_id | station_id | code | network_code | network_region | network_name | active | dispatch_type | capacity_registered | registered | deregistered | unit_id | unit_number | unit_alias | unit_capacity | approved | approved_by | approved_at | emissions_factor_co2 | interconnector | interconnector_region_to | data_first_seen | data_last_seen | expected_closure_date | expected_closure_year | interconnector_region_from | emission_factor_source | include_in_geojson |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| opennem.init | 2021-04-13 13:47:32.235400+00:00 | 2024-06-07 13:12:21.170368+00:00 | 659 | NEM | gas_ocgt | retired | 481 | LYGS6 | None | VIC1 | None | True | GENERATOR | None | None | None | None | None | None | None | True | None | None | 0.8715465 | False | None | None | None | None | None | None | None | True |
| opennem.registry | 2020-12-09 15:33:31.317149+00:00 | 2023-03-31 04:50:58.019264+00:00 | 124 | NEM | wind | operating | 95 | CROOKWF2 | NEM | NSW1 | None | True | GENERATOR | 96.0 | None | None | None | None | None | None | True | None | 2020-12-09 15:33:31.317135+00:00 | 0.0 | False | None | 2018-08-13 22:50:00+00:00 | 2024-08-03 00:50:00+00:00 | None | None | None | None | True |
| opennem.registry | 2020-12-09 15:34:56.130478+00:00 | 2024-06-07 13:12:35.255359+00:00 | 562 | WEM | gas_ocgt | operating | 403 | NEWGEN_NEERABUP_GT1 | WEM | WEM | None | True | GENERATOR | 342.0 | 2009-10-19 00:00:00 | None | None | None | None | None | True | None | 2020-12-09 15:34:56.130395+00:00 | 0.6 | False | None | 2013-12-17 01:30:00+00:00 | 2024-08-01 23:55:00+00:00 | None | None | None | None | True |
| opennem.registry | 2020-12-09 15:33:46.984866+00:00 | 2024-06-07 13:11:22.484726+00:00 | 218 | NEM | bioenergy_biogas | operating | 160 | JACKSGUL | NEM | NSW1 | None | True | GENERATOR | 2.0 | None | None | None | None | None | None | True | None | 2020-12-09 15:33:46.984840+00:00 | 0.62 | False | None | None | None | None | None | None | None | True |
| opennem.init | 2023-01-09 03:14:56.467347+00:00 | 2024-06-07 13:12:13.493276+00:00 | 759 | NEM | wind | operating | 451 | BRYB2WF2 | None | VIC1 | None | True | GENERATOR | 109.0 | None | None | None | 26 | None | 4.038 | False | None | None | 0.0 | False | None | 2022-11-28 21:50:00+00:00 | 2024-08-03 00:45:00+00:00 | None | None | None | None | True |

## Table: facility_scada

Total rows: 769,211,725

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

| network_id | interval | facility_code | generated | eoi_quantity | is_forecast | energy_quality_flag | energy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NEM | 2013-06-22 18:30:00 | URANQ14 | 0.0 | None | False | 1 | 0E-20 |
| NEM | 2024-04-08 18:55:00 | PIBESSG1 | 0.0 | 0.0 | False | 0 | 0E-20 |
| NEM | 2003-07-16 06:55:00 | TARONG#3 | 347.75 | 175.78125 | False | 1 | 28.9166666666666667 |
| NEM | 2009-03-12 17:50:00 | UPPTUMUT | 0.0 | None | False | 1 | 0E-20 |
| NEM | 2017-10-10 05:40:00 | MLSP1 | 0.138001 | None | False | 1 | 0.01150008333333333333 |

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
| cancelled | Cancelled |
| operating | Operating |
| retired | Retired |
| announced | Announced |
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

### Sample Data

| id | subject | description | email | twitter | user_ip | user_agent | created_at | alert_sent |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 75 | Queanbeyan Battery facility feedback | 
**No email provided.**
   

**Path:**
/facility/au/NEM/QBYNB/?range=3d&interval=30m

**Sources:**
Qbess is gpga its 10mw 20mwh the capital batrery is NEON not sure rating but think its about 100mw th... | None | None | 172.19.0.1 | Mozilla/5.0 (Linux; Android 13; SAMSUNG SM-A525F) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/21.0 Chrome/110.0.5481.154 Mobile Safari/537.36 | 2023-12-08 21:48:13.557640+00:00 | False |
| 62 | Collector facility feedback | 
**No email provided.**
   

**Path:**
/facility/au/NEM/COLWF01/?range=1y&interval=1w

**Sources:**
https://ratchaustralia.com/collector/

**Fields:**

```
[
 {
  "key": "COLWF01 reg cap",
  "value": ... | None | None | 172.19.0.1 | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.57 | 2023-07-01 08:01:27.418176+00:00 | False |
| 46 | Woolooga facility feedback | 
**Email:**
west45-7@hotmail.com     
   

**Path:**
/facility/au/NEM/WOOLGSF/?range=7d&interval=30m

**Sources:**
https://www.openstreetmap.org/relation/13366676

**Fields:**

```
[
 {
  "key": "Faci... | west45-7@hotmail.com | None | 172.19.0.1 | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 OPR/98.0.0.0 | 2023-05-04 00:50:25.030047+00:00 | False |
| 42 | Yarranlea facility feedback | 
**No email provided.**
   

**Path:**
/facility/au/NEM/YARANSF/?range=30d&interval=1d

**Sources:**
yarranlea facilities market turnover calculation for the day of 4 October.   Value is much too high... | None | None | 121.45.192.211 | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36 | 2021-10-05 07:08:12.480583+00:00 | True |
| 74 | Bouldercombe Battery facility feedback | 
**No email provided.**
   

**Path:**
/facility/au/NEM/BBATTERY/?range=7d&interval=30m

**Sources:**
Registered capacity needs updating

**Fields:**

```
[]
```

**Description:**
Hello, Bouldercombe ... | None | None | 172.19.0.1 | Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.60 | 2023-11-17 00:50:48.921739+00:00 | False |

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

| created_by | created_at | updated_at | code | label | renewable | fueltech_group_id |
| --- | --- | --- | --- | --- | --- | --- |
| None | 2020-12-09 01:46:29.027817+00:00 | 2022-10-04 06:24:38.567367+00:00 | battery_discharging | Battery (Discharging) | True | battery_discharging |
| None | 2020-12-09 01:46:29.376830+00:00 | 2022-10-04 06:24:38.865319+00:00 | gas_ccgt | Gas (CCGT) | False | gas |
| None | 2020-12-09 01:46:29.788923+00:00 | 2022-10-04 06:24:39.228913+00:00 | solar_utility | Solar (Utility) | True | solar |
| None | 2020-12-09 01:46:29.671803+00:00 | 2022-10-04 06:24:39.132031+00:00 | hydro | Hyrdo | True | hydro |
| None | 2020-12-09 01:46:29.435849+00:00 | 2022-10-04 06:24:38.917529+00:00 | gas_ocgt | Gas (OCGT) | False | gas |

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

| created_by | created_at | updated_at | code | label | color | renewable |
| --- | --- | --- | --- | --- | --- | --- |
| None | 2022-10-04 06:24:38.114476+00:00 | 2024-08-13 02:51:57.357664+00:00 | wind | Wind | #417505 | True |
| None | 2022-10-04 06:24:38.363459+00:00 | None | distillate | Distillate | #F35020 | False |
| None | 2022-10-04 06:24:38.461796+00:00 | 2024-08-13 02:51:57.973473+00:00 | pumps | Pumps | #88AFD0 | True |
| None | 2022-10-04 06:24:38.013420+00:00 | None | coal | Coal | #4a4a4a | False |
| None | 2022-10-04 06:24:38.214596+00:00 | 2024-08-13 02:51:57.574303+00:00 | battery_charging | Battery (Charging) | #B2DAEF | True |

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

| f_table_catalog | f_table_schema | f_table_name | f_geometry_column | coord_dimension | srid | type |
| --- | --- | --- | --- | --- | --- | --- |
| opennem | public | bom_station | geom | 2 | 4326 | POINT |
| opennem | public | location | geom | 2 | 4326 | POINT |
| opennem | public | location | boundary | 2 | 4326 | POLYGON |

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

| id | address1 | address2 | locality | state | postcode | place_id | geocode_approved | geocode_skip | geocode_processed_at | geocode_by | geom | osm_way_id | boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 13594 |  |  |  | QLD | None | None | True | False | None | opennem.registry | 0101000020E6100000B0FECF613E8D6240B83CD68C0C1237C0 | None | None |
| 13464 |  |  |  | NSW | None | None | True | False | None | opennem.registry | 0101000020E6100000212328B875AD614088D972057FFC3FC0 | None | None |
| 13806 | None | None | Eastern Creek | NSW | 2766 | None | False | False | None | None | 0101000020E6100000397EDF0B79DA62409CC4310CA3E840C0 | None | None |
| 13750 |  |  |  | SA | None | None | True | False | None | opennem.registry | 0101000020E610000080457EFD90516140CCD24ECDE56A41C0 | None | None |
| 13510 |  |  |  | NSW | None | None | True | False | None | opennem.registry | 0101000020E61000003161342BDBB26240ED66463F1A4641C0 | None | None |

## Table: milestones

Total rows: 15,123

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

| instance_id | record_id | interval | significance | value | network_id | fueltech_id | description | period | aggregate | metric | value_unit | description_long | network_region | previous_instance_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7949a2db-e2b6-4b66-87b5-e83fe6ebc760 | au.nem.sa1.power.interval.high | 2009-01-29 14:55:00 | 3 | 3218.63843 | NEM | None | Interval power high record for NEM in South Australia | interval | high | power | MW | None | SA1 | 43351624-3c68-45e5-874b-61ab8f2e04ce |
| aef13063-8925-4185-8c99-aef2ba6314fe | au.nem.tas1.power.interval.low | 2006-01-25 23:20:00 | 3 | 567.38 | NEM | None | Interval power low record for NEM in Tasmania | interval | low | power | MW | None | TAS1 | 0181514c-c45b-41d1-90ac-02bbd8bbdfec |
| 91468a98-b9f3-475a-be24-ef3d5ea8eff8 | au.nem.nsw1.hydro.energy.quarter.low | 2015-04-01 00:00:00 | 1 | 322490.613 | NEM | hydro | Quarterly hyrdo energy low record for NEM in New South Wales | quarter | low | energy | MWh | None | NSW1 | None |
| 0936139b-fb45-4b16-8c82-feb7709d0a71 | au.wem.solar.energy.day.high | 2015-08-14 00:00:00 | 9 | 587.8447 | WEM | solar | Daily solar energy high record for WEM | day | high | energy | MWh | None | None | 75b61f58-ec91-41d1-8314-ca3d1f427561 |
| 68f0c183-2648-4788-b5d4-144b721a9f80 | au.wem.bioenergy.emissions.day.low | 2016-05-22 00:00:00 | 8 | 14.1699 | WEM | bioenergy | Daily bioenergy emissions low record for WEM | day | low | emissions | tCO2e | None | None | ec34c7ce-ab47-4623-8b9a-cef7d0267f95 |

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

| trading_day | network_id | network_region | fueltech_code | generated | energy | emissions | emissions_intensity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2020-07-11 00:00:00 | NEM | SA1 | gas_ccgt | 186193.6453 | 15516.1647 | 7656.2850 | 0.4934 |
| 2018-03-14 00:00:00 | WEM | WEM | gas_ocgt | 34931.4130 | 17509.1345 | 10874.0532 | 0.6211 |
| 2002-10-29 00:00:00 | NEM | VIC1 | coal_brown | 1693980.8900 | 140917.9612 | 181520.9902 | 1.2881 |
| 2008-05-28 00:00:00 | NEM | QLD1 | hydro | 40567.5257 | 3381.2492 | 0.0000 | 0.0000 |
| 2009-03-28 00:00:00 | NEM | SA1 | gas_steam | 15110.0483 | 1259.3286 | 892.3099 | 0.7086 |

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

| observation_time | station_id | temp_air | temp_min | temp_max |
| --- | --- | --- | --- | --- |
| 2021-02-03 00:30:00+00:00 | 063292 | 16.2000000000000000 | 16.2 | 16.2 |
| 2020-12-22 05:00:00+00:00 | 009215 | 28.4000000000000000 | 28.4 | 28.4 |
| 2021-04-20 20:30:00+00:00 | 040004 | 10.7000000000000000 | 10.7 | 10.7 |
| 2023-04-14 23:00:00+00:00 | 014015 | 29.0000000000000000 | 29.0 | 29.0 |
| 2021-01-08 15:00:00+00:00 | 085096 | 16.8000000000000000 | 16.8 | 16.8 |

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

| created_by | created_at | updated_at | code | country | label | timezone | interval_size | offset | timezone_database | export_set | interval_shift | network_price | data_start_date | data_end_date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| None | 2020-12-09 01:46:31.057929+00:00 | 2024-08-10 04:32:14.138129+00:00 | NEM | au | NEM | Australia/Brisbane | 5 | 600 | AEST | True | 5 | NEM | 1998-12-06 15:40:00+00:00 | 2024-08-03 00:15:00+00:00 |
| None | 2020-12-09 01:46:31.176786+00:00 | 2024-08-03 00:15:22.319623+00:00 | APVI | au | APVI | Australia/Perth | 15 | 600 | AWST | False | 0 | WEM | 2015-03-19 20:15:00+00:00 | 2024-08-03 00:00:00+00:00 |
| None | 2023-02-22 09:54:49.679305+00:00 | 2024-08-10 04:32:14.781558+00:00 | OPENNEM_ROOFTOP_BACKFILL | au | OpenNEM Rooftop Backfill | Australia/Brisbane | 30 | 600 | AEST | False | 0 | NEM | 2015-03-19 20:15:00+00:00 | 2018-02-28 09:30:00+00:00 |
| None | 2021-04-12 07:06:18.835747+00:00 | 2024-08-10 04:32:14.674557+00:00 | AEMO_ROOFTOP_BACKFILL | au | AEMO Rooftop Backfill | Australia/Brisbane | 30 | 600 | AEST | False | 0 | NEM | None | None |
| None | 2021-04-09 10:15:56.408641+00:00 | 2024-08-10 04:32:14.576316+00:00 | AEMO_ROOFTOP | au | AEMO Rooftop | Australia/Brisbane | 30 | 600 | AEST | False | 0 | NEM | 2016-07-31 14:30:00+00:00 | 2024-08-02 23:30:00+00:00 |

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

| created_by | created_at | updated_at | network_id | code | timezone | timezone_database | offset | export_set |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| None | 2020-12-09 01:46:31.302424+00:00 | None | NEM | NSW1 | None | None | None | True |
| None | 2020-12-09 01:46:31.239865+00:00 | None | WEM | WEM | None | None | None | True |
| None | 2021-04-09 10:15:56.438248+00:00 | None | AEMO_ROOFTOP | QLD1 | None | None | None | True |
| None | 2020-12-09 01:46:31.422815+00:00 | None | NEM | VIC1 | None | None | None | True |
| None | 2024-08-10 04:32:14.952549+00:00 | None | WEM | WEMDE | None | None | None | True |

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

| participantid | participantclassid | name | id | description | code | acn | primarybusiness | name | lastchanged | network_name | network_code | country | abn | approved | approved_by | approved_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 62 | HBJMIN | HBJMineralsPty | None | None | None | None | False | None | None |
| 163 | Phoenix | PhoenixEnergy | None | None | None | None | False | None | None |
| 137 | Imowa | AustralianEnergyMarketOperator | None | None | None | None | False | None | None |
| 13 | LNDFLLGP | LandfillGasandPowerPty | Landfill Gas And Power Pty Ltd | None | None | None | False | None | 2021-01-15 04:20:48.442175+00:00 |
| 95 | Astar | AStarElectricity | None | None | None | None | False | None | None |

## Table: pg_stat_statements

Total rows: 126

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

| userid | dbid | toplevel | queryid | query | plans | total_plan_time | min_plan_time | max_plan_time | mean_plan_time | stddev_plan_time | calls | total_exec_time | min_exec_time | max_exec_time | mean_exec_time | stddev_exec_time | rows | shared_blks_hit | shared_blks_read | shared_blks_dirtied | shared_blks_written | local_blks_hit | local_blks_read | local_blks_dirtied | local_blks_written | temp_blks_read | temp_blks_written | blk_read_time | blk_write_time | wal_records | wal_fpi | wal_bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 16384 | 16448 | True | -5843739379638153553 | CREATE TEMP TABLE __tmp_facility_scada_20240909222046
    (LIKE facility_scada INCLUDING DEFAULTS)
    ON COMMIT DROP | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 14.263385 | 14.263385 | 14.263385 | 14.263385 | 0.0 | 0 | 525 | 57 | 24 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.0 | 104 | 25 | 150370 |
| 16384 | 16448 | True | 8401511264330023979 | COPY "__tmp_facility_scada_20240909222046"("network_id", "interval", "facility_code", "generated", "eoi_quantity", "is_forecast", "energy_quality_flag", "energy") FROM STDIN (FORMAT binary) | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 11.283371 | 11.283371 | 11.283371 | 11.283371 | 0.0 | 466 | 0 | 0 | 0 | 0 | 5 | 0 | 6 | 6 | 0 | 0 | 0.0 | 0.0 | 0 | 0 | 0 |
| 16384 | 16448 | True | 7146888456859552635 | SELECT * FROM balancing_summary ORDER BY RANDOM() LIMIT $1 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2 | 14703.377012 | 7085.659937 | 7617.717075 | 7351.688506 | 266.02856899999983 | 10 | 8746 | 237428 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.0 | 0 | 0 | 0 |
| 16384 | 16448 | True | -5555279242663759534 | SELECT * FROM feedback ORDER BY RANDOM() LIMIT $1 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2 | 0.252615 | 0.10732699999999999 | 0.145288 | 0.1263075 | 0.0189805 | 10 | 14 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.0 | 0 | 0 | 0 |
| 16384 | 16448 | True | 396979206045734760 | INSERT INTO facility_scada
        SELECT *
        FROM __tmp_facility_scada_20240909224046
    ON CONFLICT 
    (network_id,interval,facility_code,is_forecast) DO UPDATE set generated = EXCLUDED.gen... | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 | 128.082273 | 128.082273 | 128.082273 | 128.082273 | 0.0 | 461 | 16256 | 553 | 536 | 22 | 6 | 0 | 0 | 0 | 0 | 0 | 0.0 | 0.0 | 6114 | 515 | 3732690 |

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

| dealloc | stats_reset |
| --- | --- |
| 0 | 2024-09-09 22:19:07.454676+00:00 |

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

| srid | auth_name | auth_srid | srtext | proj4text |
| --- | --- | --- | --- | --- |
| 32011 | EPSG | 32011 | PROJCS["NAD27 / New Jersey",GEOGCS["NAD27",DATUM["North_American_Datum_1927",SPHEROID["Clarke 1866",6378206.4,294.9786982138982,AUTHORITY["EPSG","7008"]],AUTHORITY["EPSG","6267"]],PRIMEM["Greenwich",0... | +proj=tmerc +lat_0=38.83333333333334 +lon_0=-74.66666666666667 +k=0.9999749999999999 +x_0=609601.2192024384 +y_0=0 +datum=NAD27 +units=us-ft +no_defs  |
| 2633 | EPSG | 2633 | PROJCS["Pulkovo 1942 / 3-degree Gauss-Kruger CM 171E",GEOGCS["Pulkovo 1942",DATUM["Pulkovo_1942",SPHEROID["Krassowsky 1940",6378245,298.3,AUTHORITY["EPSG","7024"]],TOWGS84[23.92,-141.27,-80.9,0,0.35,0... | +proj=tmerc +lat_0=0 +lon_0=171 +k=1 +x_0=500000 +y_0=0 +ellps=krass +towgs84=23.92,-141.27,-80.9,0,0.35,0.82,-0.12 +units=m +no_defs  |
| 4584 | EPSG | 4584 | PROJCS["New Beijing / Gauss-Kruger CM 105E",GEOGCS["New Beijing",DATUM["New_Beijing",SPHEROID["Krassowsky 1940",6378245,298.3,AUTHORITY["EPSG","7024"]],AUTHORITY["EPSG","1045"]],PRIMEM["Greenwich",0,A... | +proj=tmerc +lat_0=0 +lon_0=105 +k=1 +x_0=500000 +y_0=0 +ellps=krass +units=m +no_defs  |
| 26977 | EPSG | 26977 | PROJCS["NAD83 / Kansas North",GEOGCS["NAD83",DATUM["North_American_Datum_1983",SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","6269"]],PRIM... | +proj=lcc +lat_1=39.78333333333333 +lat_2=38.71666666666667 +lat_0=38.33333333333334 +lon_0=-98 +x_0=400000 +y_0=0 +datum=NAD83 +units=m +no_defs  |
| 2698 | EPSG | 2698 | PROJCS["Pulkovo 1995 / 3-degree Gauss-Kruger zone 64",GEOGCS["Pulkovo 1995",DATUM["Pulkovo_1995",SPHEROID["Krassowsky 1940",6378245,298.3,AUTHORITY["EPSG","7024"]],TOWGS84[24.47,-130.89,-81.56,0,0,0.1... | +proj=tmerc +lat_0=0 +lon_0=-168 +k=1 +x_0=64500000 +y_0=0 +ellps=krass +towgs84=24.47,-130.89,-81.56,0,0,0.13,-0.22 +units=m +no_defs  |

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

| created_by | stationid | created_at | stationname | address1 | updated_at | address2 | id | address3 | participant_id | address4 | location_id | code | city | state | name | description | postcode | lastchanged | wikipedia_link | connectionpointid | wikidata_id | network_code | network_name | approved | approved_by | approved_at | website_url |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| opennem.init | 2021-04-13 13:47:32.790389+00:00 | 2024-06-07 13:11:26.790387+00:00 | 482 | None | 4882 | NORTHGT | Northern | None | None | None | None | NORTHERN GAS TURBINE | True | opennem.importer.facilities | 2024-06-07 23:11:26.837534+00:00 | None |
| opennem.registry | 2020-12-09 15:32:39.826093+00:00 | 2024-06-07 13:12:03.971136+00:00 | 335 | None | 13750 | WINGF1 | Wingfield | None | None | None | None | Wingfield 1 | True | opennem.importer.facilities | 2024-06-07 23:12:04.020536+00:00 | None |
| opennem.init | 2020-12-15 07:00:22.523039+00:00 | 2024-06-07 13:12:19.831638+00:00 | 425 | None | 1225 | KIAMSF1 | Kiamal | Kiamal Solar Farm is located in north-west Victoria, approximately 3 km north of the township of Ouyen with Stage 1 currently under construction. When completed it will be Victoria's largest solar far... | None | None | None | Kiamal Solar Farm | True | opennem.importer.facilities | 2024-06-07 23:12:19.876389+00:00 | None |
| opennem.registry | 2020-12-09 15:32:39.826093+00:00 | 2024-06-07 13:11:51.730127+00:00 | 338 | None | 13753 | WIVENSH | Wivenhoe | None | None | None | None | Wivenhoe (Mini Hydro) | True | opennem.importer.facilities | 2024-06-07 23:11:51.775443+00:00 | None |
| opennem.registry | 2020-12-09 15:32:39.826093+00:00 | 2024-06-07 13:11:34.171269+00:00 | 328 | None | 13743 | WG | Warragamba | Warragamba Power Station is a hydroelectric power station at Warragamba Dam, New South Wales, Australia. Warragamba has one turbine with a generating capacity of 50 MW of electricity.
The power statio... | https://en.wikipedia.org/wiki/Warragamba_Power_Station | Q7969919 | None | Warragamba | True | opennem.importer.facilities | 2024-06-07 23:11:34.218057+00:00 | None |

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

| created_by | created_at | updated_at | stat_date | country | stat_type | value |
| --- | --- | --- | --- | --- | --- | --- |
| None | 2021-01-05 09:47:54.294658+00:00 | None | 2020-03-31 00:00:00+00:00 | au | CPI | 116.6 |
| None | 2021-01-05 09:47:54.294658+00:00 | None | 1976-03-31 00:00:00+00:00 | au | CPI | 17.3 |
| None | 2021-01-05 09:47:54.294658+00:00 | None | 2009-12-31 00:00:00+00:00 | au | CPI | 94.3 |
| None | 2021-01-05 09:47:54.294658+00:00 | None | 1998-06-30 00:00:00+00:00 | au | CPI | 67.4 |
| None | 2021-01-05 09:47:54.294658+00:00 | None | 2016-03-31 00:00:00+00:00 | au | CPI | 108.2 |

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

| id | task_name | time_start | time_end | time_sql | time_cpu | errors | retention_period | level | invokee_name |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5f1235f7-8907-430c-aa50-80e134c4e287 | wem_per_interval_check | 2024-02-19 21:59:32.441921+00:00 | 2024-02-19 21:59:50.447996+00:00 | None | None | 0 | forever | noisy |  |
| 7cdda960-1f4b-4df8-912b-f7aea1dd905c | wem_per_interval_check | 2024-04-20 22:27:43.434531+00:00 | 2024-04-20 22:28:00.804758+00:00 | None | None | 0 | forever | noisy |  |
| 4a691c0b-bce5-4688-881e-342d361bb4f9 | nem_dispatch_scada_crawl | 2024-05-01 16:30:16.425898+00:00 | 2024-05-01 16:33:26.039223+00:00 | None | None | 0 | forever | noisy |  |
| 2103958e-afc3-428f-adbb-955c8a3d41fb | run_aggregate_flow_for_interval_v3 | 2024-05-07 03:40:01.450143+00:00 | 2024-05-07 03:40:01.548578+00:00 | None | None | 0 | forever | info |  |
| 649ad23d-b391-4725-9cd2-958b4d2f89a0 | run_aggregate_flow_for_interval_v3 | 2024-03-25 22:30:05.051527+00:00 | 2024-03-25 22:30:05.156517+00:00 | None | None | 0 | forever | info |  |
