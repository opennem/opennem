# Database Schema

Database: opennem
PostgreSQL version: PostgreSQL 17.0 (Ubuntu 17.0-1.pgdg24.04+1) on x86_64-pc-linux-gnu, compiled by gcc (Ubuntu 13.2.0-23ubuntu4) 13.2.0, 64-bit
Schemas: public

## Table of Contents

| Schema | Table Name | Row Count |
|--------|------------|----------|
| public | [aemo_market_notices](#public-aemo-market-notices) | 0 |
| public | [alembic_version](#public-alembic-version) | 1 |
| public | [at_facility_intervals](#public-at-facility-intervals) | 346,757,426 |
| public | [at_network_demand](#public-at-network-demand) | 63,418 |
| public | [at_network_flows](#public-at-network-flows) | 8,067,005 |
| public | [balancing_summary](#public-balancing-summary) | 11,422,029 |
| public | [bom_observation](#public-bom-observation) | 5,958,559 |
| public | [bom_station](#public-bom-station) | 773 |
| public | [crawl_history](#public-crawl-history) | 358,642 |
| public | [crawl_meta](#public-crawl-meta) | 51 |
| public | [facilities](#public-facilities) | 555 |
| public | [facility_scada](#public-facility-scada) | 782,047,361 |
| public | [facility_status](#public-facility-status) | 12 |
| public | [feedback](#public-feedback) | 126 |
| public | [fueltech](#public-fueltech) | 26 |
| public | [fueltech_group](#public-fueltech-group) | 10 |
| public | [milestones](#public-milestones) | 0 |
| public | [network](#public-network) | 6 |
| public | [network_region](#public-network-region) | 11 |
| public | [stats](#public-stats) | 403 |
| public | [units](#public-units) | 856 |

## Enabled PostgreSQL Plugins

| Plugin Name | Version |
|-------------|--------|
| hstore | 1\.6 |
| pg\_stat\_statements | 1\.9 |
| plpgsql | 1\.0 |
| postgis | 3\.5\.0 |
| postgis\_raster | 3\.1\.4 |
| postgis\_topology | 3\.5\.0 |
| timescaledb | 2\.17\.1 |

## Table: public.aemo_market_notices

Total rows: 0

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
| ea9674fa02bb |

## Table: public.at_facility_intervals

Total rows: 346,757,845

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| interval | timestamp without time zone | N/A | No |
| network_id | text | N/A | No |
| facility_code | text | N/A | No |
| unit_code | text | N/A | No |
| fueltech_code | text | N/A | No |
| network_region | text | N/A | No |
| status_id | text | N/A | Yes |
| generated | double precision | N/A | Yes |
| energy | double precision | N/A | Yes |
| emissions | double precision | N/A | Yes |
| emissions_intensity | double precision | N/A | Yes |
| market_value | double precision | N/A | Yes |
| last_updated | timestamp with time zone | N/A | No |

### Create Table Statement

```sql
CREATE TABLE public.at_facility_intervals
(
    "interval" timestamp without time zone NOT NULL,
    network_id text NOT NULL,
    facility_code text NOT NULL,
    unit_code text NOT NULL,
    fueltech_code text NOT NULL,
    network_region text NOT NULL,
    status_id text,
    generated double precision,
    energy double precision,
    emissions double precision,
    emissions_intensity double precision,
    market_value double precision,
    last_updated timestamp with time zone NOT NULL
);

```

### Constraints

- PRIMARY KEY ("interval", network_id, facility_code, unit_code)
- FOREIGN KEY (network_id) REFERENCES network(code)

### Indexes

- CREATE UNIQUE INDEX at_facility_intervals_pkey ON public.at_facility_intervals USING btree ("interval", network_id, facility_code, unit_code)
- CREATE INDEX idx_at_facility_intervals_facility_interval ON public.at_facility_intervals USING btree (facility_code, "interval" DESC)
- CREATE INDEX idx_at_facility_intervals_interval_network ON public.at_facility_intervals USING btree ("interval" DESC, network_id)
- CREATE INDEX idx_at_facility_intervals_network_region ON public.at_facility_intervals USING btree (network_region)
- CREATE INDEX idx_at_facility_intervals_time_facility ON public.at_facility_intervals USING btree ("interval" DESC, facility_code)
- CREATE INDEX idx_at_facility_intervals_unit_time ON public.at_facility_intervals USING btree (unit_code, "interval" DESC)
- CREATE INDEX ix_at_facility_intervals_facility_code ON public.at_facility_intervals USING btree (facility_code)
- CREATE INDEX ix_at_facility_intervals_network_id ON public.at_facility_intervals USING btree (network_id)
- CREATE INDEX ix_at_facility_intervals_unit_code ON public.at_facility_intervals USING btree (unit_code)

### Sample Data

| interval | network\_id | facility\_code | unit\_code | fueltech\_code | network\_region | status\_id | generated | energy | emissions | emissions\_intensity | market\_value | last\_updated |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014\-10\-21 13:30:00 | NEM | MEADOWBK | MEADOWBK | hydro | TAS1 | operating | 0\.0 | 0\.0 | 0\.0 | 0\.0 | 0\.0 | 2024\-11\-14 05:35:38\.117264\+00:00 |
| 2021\-06\-15 13:25:00 | NEM | DDSF | DDSF1 | solar\_utility | QLD1 | operating | 57\.5754 | 5\.3254 | 0\.0 | 0\.0 | 536\.4276 | 2024\-11\-13 22:13:12\.427641\+00:00 |
| 2024\-09\-09 14:55:00 | NEM | DDSF | DDSF1 | solar\_utility | QLD1 | operating | 71\.2909 | 5\.9796 | 0\.0 | 0\.0 | 499\.2408 | 2024\-11\-12 22:12:45\.871117\+00:00 |
| 2018\-01\-06 02:10:00 | NEM | KAREEYA | KAREEYA1 | hydro | QLD1 | operating | 0\.0 | 0\.0 | 0\.0 | 0\.0 | 0\.0 | 2024\-11\-14 01:40:31\.868550\+00:00 |
| 2022\-09\-16 12:05:00 | NEM | LKBONNY1 | LKBONNY1 | wind | SA1 | operating | 0\.0 | 0\.0 | 0\.0 | 0\.0 | 0\.0 | 2024\-11\-13 19:33:35\.047518\+00:00 |

## Table: public.at_network_demand

Total rows: 63,418

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
- CREATE INDEX idx_at_network_demand_network_id_trading_interval ON public.at_network_demand USING btree (network_id, trading_day)
- CREATE INDEX idx_at_network_demand_trading_interval_network_region ON public.at_network_demand USING btree (trading_day, network_id, network_region)
- CREATE INDEX ix_at_network_demand_network_id ON public.at_network_demand USING btree (network_id)
- CREATE INDEX ix_at_network_demand_trading_day ON public.at_network_demand USING btree (trading_day)

### Sample Data

| trading\_day | network\_id | network\_region | demand\_energy | demand\_market\_value |
| --- | --- | --- | --- | --- |
| 2006\-05\-01 00:00:00\+00:00 | NEM | SA1 | 31\.99070916666666666668 | 112068\.6619916666666671678000 |
| 2020\-02\-07 00:00:00\+00:00 | NEM | VIC1 | 123\.33699691416666666665 | 5605281\.9762820920499993053308000 |
| 2014\-02\-02 00:00:00\+00:00 | NEM | QLD1 | 130\.47398119166666666670 | 6129755\.1144127517250012004553000 |
| 2000\-10\-25 00:00:00\+00:00 | NEM | QLD1 | 19\.92614833333333333333 | 1509843\.9918333333333337045000 |
| 2016\-09\-26 00:00:00\+00:00 | NEM | SNOWY1 | None | None |

## Table: public.at_network_flows

Total rows: 8,067,020

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
- CREATE INDEX idx_at_network_flowsy_network_id_trading_interval ON public.at_network_flows USING btree (network_id, trading_interval)
- CREATE INDEX idx_at_network_flows_trading_interval_facility_code ON public.at_network_flows USING btree (trading_interval, network_id, network_region)
- CREATE INDEX ix_at_network_flows_network_id ON public.at_network_flows USING btree (network_id)
- CREATE INDEX ix_at_network_flows_network_region ON public.at_network_flows USING btree (network_region)
- CREATE INDEX ix_at_network_flows_trading_interval ON public.at_network_flows USING btree (trading_interval)

### Sample Data

| trading\_interval | network\_id | network\_region | energy\_imports | energy\_exports | emissions\_imports | emissions\_exports | market\_value\_imports | market\_value\_exports |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2021\-05\-13 09:20:00\+00:00 | NEM | NSW1 | 0\.0 | 25\.9704425 | 0\.0 | 18\.64262800929266 | 0\.0 | 0\.0 |
| 2009\-07\-26 15:55:00\+00:00 | NEM | TAS1 | 0\.0 | 20\.75 | 0\.0 | 0\.0 | 0\.0 | 0\.0 |
| 2010\-09\-18 14:15:00\+00:00 | NEM | TAS1 | 0\.0 | 28\.5 | 0\.0 | 0\.0 | 0\.0 | 0\.0 |
| 2019\-05\-25 20:00:00\+00:00 | NEM | VIC1 | 6\.149775833333333 | 48\.229884166666665 | 0\.9773668894844824 | 48\.647516511035015 | 0\.0 | 0\.0 |
| 2024\-04\-30 16:25:00\+00:00 | NEM | VIC1 | 30\.591565833333334 | 36\.2666675 | 5\.425150055202556 | 28\.4274656055372 | 0\.0 | 0\.0 |

## Table: public.balancing_summary

Total rows: 11,422,039

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
| is_forecast | boolean | N/A | No |
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
    is_forecast boolean NOT NULL,
    net_interchange numeric,
    demand_total numeric,
    price_dispatch numeric,
    net_interchange_trading numeric,
    demand numeric
);

```

### Constraints

- PRIMARY KEY ("interval", network_id, network_region, is_forecast)

### Indexes

- CREATE INDEX ix_balancing_summary_network_region ON public.balancing_summary USING btree (network_region)
- CREATE UNIQUE INDEX pk_balancing_summary_pkey ON public.balancing_summary USING btree ("interval", network_id, network_region, is_forecast)
- CREATE INDEX ix_balancing_summary_interval ON public.balancing_summary USING btree ("interval")
- CREATE INDEX idx_balancing_summary_interval_network_region ON public.balancing_summary USING btree ("interval" DESC, network_id, network_region)
- CREATE INDEX idx_balancing_price_lookup ON public.balancing_summary USING btree ("interval", network_id, network_region, price) WHERE ((is_forecast = false) AND (price IS NOT NULL))
- CREATE INDEX idx_balancing_region_time ON public.balancing_summary USING btree (network_region, "interval", is_forecast)
- CREATE INDEX idx_balancing_time_lookup ON public.balancing_summary USING btree ("interval", network_id, network_region, is_forecast)

### Sample Data

| interval | network\_id | network\_region | forecast\_load | generation\_scheduled | generation\_non\_scheduled | generation\_total | price | is\_forecast | net\_interchange | demand\_total | price\_dispatch | net\_interchange\_trading | demand |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2018\-11\-19 16:10:00 | NEM | QLD1 | None | None | None | None | 100\.94097 | False | 309\.48 | 6596\.5915 | 100\.94097 | None | 6509\.53 |
| 2023\-08\-24 13:15:00 | NEM | TAS1 | None | None | None | None | \-39\.54 | False | \-410\.18 | 1139\.801170 | \-39\.53869 | None | 1007\.73 |
| 2012\-10\-20 07:40:00 | NEM | VIC1 | None | None | None | None | 46\.61352 | False | 1121\.78 | 5079\.228 | 46\.61352 | None | 4896\.84 |
| 2016\-02\-12 08:15:00 | NEM | QLD1 | None | None | None | None | 35\.11006 | False | 125\.97 | 6844\.14125 | 35\.11006 | None | 6707\.88 |
| 2016\-11\-11 11:45:00 | NEM | VIC1 | None | None | None | None | 37\.91748 | False | 1152\.77 | 5200\.1750 | 37\.91748 | None | 5109\.78 |

## Table: public.bom_observation

Total rows: 5,958,559

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
| 2021\-04\-22 07:00:00\+00:00 | 040958 | 19\.0 | 20\.3 | 1013\.2 | NW | 9 |  |  | 56 | 13 | None | None |
| 2022\-04\-29 07:30:00\+00:00 | 070351 | 16\.2 | 18\.3 | 1019\.9 | NW | 15\.0 | None | None | 69\.0 | 20\.0 | None | None |
| 2021\-01\-01 21:30:00\+00:00 | 022803 | 13\.7 | 16\.6 | 1012\.0 | SSW | 22 |  |  | 84 | 32 | None | None |
| 2021\-02\-01 08:40:00\+00:00 | 250061 | 31\.1 | 27\.7 | None | NNE | 6 |  |  | 70 | 7 | None | None |
| 2021\-01\-22 14:00:00\+00:00 | 010692 | 17\.1 | 18\.9 | 1003\.7 | SE | 15 |  |  | 70 | 20 | None | None |

## Table: public.bom_station

Total rows: 773

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| code | text | N/A | No |
| state | text | N/A | No |
| name | text | N/A | No |
| registered | date | N/A | Yes |
| geom | USER-DEFINED | N/A | Yes |
| feed_url | text | N/A | Yes |
| is_capital | boolean | N/A | No |
| name_alias | text | N/A | Yes |
| priority | integer | N/A | No |
| website_url | text | N/A | Yes |
| altitude | integer | N/A | Yes |
| web_code | text | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE public.bom_station
(
    code text NOT NULL,
    state text NOT NULL,
    name text NOT NULL,
    registered date,
    geom USER-DEFINED,
    feed_url text,
    is_capital boolean NOT NULL,
    name_alias text,
    priority integer NOT NULL,
    website_url text,
    altitude integer,
    web_code text
);

```

### Constraints

- PRIMARY KEY (code)

### Indexes

- CREATE UNIQUE INDEX bom_station_pkey ON public.bom_station USING btree (code)
- CREATE INDEX ix_bom_station_code ON public.bom_station USING btree (code)
- CREATE INDEX idx_bom_station_geom ON public.bom_station USING gist (geom)
- CREATE INDEX idx_bom_station_priority ON public.bom_station USING btree (priority)

### Sample Data

| code | state | name | registered | geom | feed\_url | is\_capital | name\_alias | priority | website\_url | altitude | web\_code |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 056229 | NSW | GUYRA HOSPITAL | None | 0101000020E6100000F6285C8FC2F56240F6285C8FC2353EC0 | http://www\.bom\.gov\.au/fwo/IDN60801/IDN60801\.94772\.json | False | Guyra | 5 | http://www\.bom\.gov\.au/products/IDN60801/IDN60801\.94772\.shtml | 1329 | None |
| 098017 | TAS | KING ISLAND AIRPORT | None | 0101000020E610000014AE47E17AFC6140713D0AD7A3F043C0 | http://www\.bom\.gov\.au/fwo/IDT60801/IDT60801\.94850\.json | False | King Island Airport | 5 | http://www\.bom\.gov\.au/products/IDT60801/IDT60801\.94850\.shtml | 35 | None |
| 009842 | WA | JARRAHWOOD | None | 0101000020E61000007B14AE47E1EA5C406666666666E640C0 | http://www\.bom\.gov\.au/fwo/IDW60801/IDW60801\.95623\.json | False | Jarrahwood | 5 | http://www\.bom\.gov\.au/products/IDW60801/IDW60801\.95623\.shtml | 130 | None |
| 086038 | VIC | ESSENDON AIRPORT | None | 0101000020E610000085EB51B81E1D62403D0AD7A370DD42C0 | http://www\.bom\.gov\.au/fwo/IDV60801/IDV60801\.95866\.json | False | Essendon Airport | 5 | http://www\.bom\.gov\.au/products/IDV60801/IDV60801\.95866\.shtml | 78 | None |
| 039059 | QLD | LADY ELLIOT ISLAND | None | 0101000020E6100000D7A3703D0A1763405C8FC2F5281C38C0 | http://www\.bom\.gov\.au/fwo/IDQ60801/IDQ60801\.94388\.json | False | Lady Elliot Island | 5 | http://www\.bom\.gov\.au/products/IDQ60801/IDQ60801\.94388\.shtml | 4 | None |

## Table: public.crawl_history

Total rows: 358,650

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
| nemweb | au\.nemweb\.current\.dispatch\_is | NEM | 2024\-03\-25 19:35:00\+00:00 | 16 | None | 2024\-03\-25 09:35:01\+00:00 |
| nemweb | au\.nemweb\.current\.dispatch\_is | NEM | 2024\-06\-21 03:25:00\+00:00 | 16 | None | 2024\-06\-20 17:25:00\+00:00 |
| nemweb | au\.nemweb\.current\.dispatch\_scada | NEM | 2024\-05\-25 13:30:00\+00:00 | 457 | None | 2024\-05\-25 03:30:17\+00:00 |
| nemweb | au\.nemweb\.current\.dispatch\_is | NEM | 2023\-12\-10 08:10:00\+00:00 | 16 | None | 2023\-12\-09 22:10:00\+00:00 |
| nemweb | au\.nemweb\.current\.dispatch\_scada | NEM | 2024\-11\-12 03:25:00\+00:00 | 450 | None | 2024\-11\-14 01:51:41\+00:00 |

## Table: public.crawl_meta

Total rows: 51

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
| au\.wemde\.current\.trading\_report | \{'last\_crawled': '2024\-11\-07T06:27:29\+11:00', 'latest\_interval': '2024\-11\-06T07:30:00\+08:00', 'latest\_processed': '2024\-01\-15T11:46:08\+11:00'\} | 2024\-01\-14 20:44:28\.291724\+00:00 | 2024\-11\-06 19:27:29\.226149\+00:00 |
| au\.nem\.dispatch\_actual\_gen | \{'version': '2', 'last\_crawled': '2022\-07\-27T11:41:09\+10:00', 'server\_latest': '2022\-07\-27T04:00:00\+10:00', 'latest\_processed': '2022\-07\-27T04:00:00\+10:00'\} | 2022\-06\-10 08:15:16\.612054\+00:00 | 2022\-07\-27 01:41:10\.819171\+00:00 |
| au\.wem\.live\.balancing | \{'version': '2', 'last\_crawled': '2024\-01\-15T07:33:53\+11:00', 'server\_latest': '2024\-01\-15T05:30:00\+08:00', 'latest\_processed': '2024\-01\-15T05:30:00\+08:00'\} | 2022\-06\-10 05:54:04\.974218\+00:00 | 2024\-01\-14 20:33:53\.360964\+00:00 |
| au\.mms\.meterdata\_gen\_duid | \{'version': '2', 'last\_crawled': '2023\-04\-01T15:21:32\+11:00'\} | 2023\-03\-30 12:12:55\.510477\+00:00 | 2023\-04\-01 04:21:32\.569705\+00:00 |
| au\.nem\.current\.trading\_is | \{'version': '2', 'last\_crawled': '2022\-06\-27T12:06:40\+10:00', 'server\_latest': '2022\-06\-27T11:05:00\+10:00', 'latest\_processed': '2022\-06\-27T11:05:00\+10:00'\} | 2022\-06\-10 06:02:31\.619474\+00:00 | 2022\-06\-27 02:43:46\.747266\+00:00 |

## Table: public.facilities

Total rows: 555

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
