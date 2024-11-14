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
| id | integer | N/A | No |
| code | text | N/A | No |
| name | text | N/A | No |
| description | text | N/A | Yes |
| wikipedia_link | text | N/A | Yes |
| wikidata_id | text | N/A | Yes |
| network_id | text | N/A | No |
| network_region | text | N/A | No |
| approved | boolean | N/A | No |
| website_url | text | N/A | Yes |

### Create Table Statement

```sql
CREATE TABLE public.facilities
(
    id integer NOT NULL,
    code text NOT NULL,
    name text NOT NULL,
    description text,
    wikipedia_link text,
    wikidata_id text,
    network_id text NOT NULL,
    network_region text NOT NULL,
    approved boolean NOT NULL,
    website_url text
);

```

### Constraints

- UNIQUE (code)
- PRIMARY KEY (id)

### Indexes

- CREATE UNIQUE INDEX excl_station_network_duid ON public.facilities USING btree (code)
- CREATE UNIQUE INDEX station_pkey ON public.facilities USING btree (id)
- CREATE UNIQUE INDEX ix_facilities_code ON public.facilities USING btree (code)

### Sample Data

| id | code | name | description | wikipedia\_link | wikidata\_id | network\_id | network\_region | approved | website\_url |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 379 | DCWL\_DENMARK | Denmark | None | None | None | WEM | WEM | True | https://www\.dcw\.net\.au/index\.htm |
| 41 | BAYSW | Bayswater | None | https://en\.wikipedia\.org/wiki/Bayswater\_Power\_Station | Q2944653 | NEM | NSW1 | True | None |
| 353 | YALLOURN | Yallourn W | None | https://en\.wikipedia\.org/wiki/Yallourn\_Power\_Station | None | NEM | VIC1 | True | https://www\.energyaustralia\.com\.au/about\-us/energy\-generation/yallourn\-power\-station |
| 188 | LONSDALE | Lonsdale | Lonsdale Power Station is a diesel\-powered electricity generator in South Australia in Lonsdale, an industrial southern suburb of Adelaide\. It is owned by Snowy Hydro since 2014\. It consists of 18 die\.\.\. | https://en\.wikipedia\.org/wiki/Lonsdale\_Power\_Station | Q48815652 | NEM | SA1 | True | None |
| 274 | SNOWNTH | Snowtown North | None | https://en\.wikipedia\.org/wiki/Snowtown\_Wind\_Farm | None | NEM | SA1 | True | https://snowtownwindfarm2\.com\.au/ |

## Table: public.facility_scada

Total rows: 782,048,285

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| network_id | text | N/A | No |
| interval | timestamp without time zone | N/A | No |
| facility_code | text | N/A | No |
| generated | numeric | N/A | Yes |
| energy | numeric | N/A | Yes |
| is_forecast | boolean | N/A | No |
| energy_quality_flag | numeric | N/A | No |

### Create Table Statement

```sql
CREATE TABLE public.facility_scada
(
    network_id text NOT NULL,
    "interval" timestamp without time zone NOT NULL,
    facility_code text NOT NULL,
    generated numeric,
    energy numeric,
    is_forecast boolean NOT NULL,
    energy_quality_flag numeric NOT NULL
);

```

### Constraints

- PRIMARY KEY ("interval", network_id, facility_code, is_forecast)

### Indexes

- CREATE UNIQUE INDEX pk_facility_scada ON public.facility_scada USING btree ("interval", network_id, facility_code, is_forecast)
- CREATE INDEX idx_facility_scada_facility_code_interval ON public.facility_scada USING btree (facility_code, "interval" DESC)
- CREATE INDEX idx_facility_scada_interval_bucket ON public.facility_scada USING btree ("interval", network_id, facility_code, is_forecast)
- CREATE INDEX idx_facility_scada_interval_facility_code ON public.facility_scada USING btree ("interval", facility_code)
- CREATE INDEX ix_facility_scada_facility_code ON public.facility_scada USING btree (facility_code)
- CREATE INDEX ix_facility_scada_interval ON public.facility_scada USING btree ("interval")
- CREATE INDEX ix_facility_scada_network_id ON public.facility_scada USING btree (network_id)
- CREATE INDEX idx_facility_scada_network_id ON public.facility_scada USING btree (network_id)
- CREATE INDEX idx_facility_scada_non_forecast ON public.facility_scada USING btree ("interval", facility_code, generated, energy) WHERE (is_forecast = false)
- CREATE INDEX idx_facility_scada_lookup ON public.facility_scada USING btree ("interval", facility_code, is_forecast) WHERE (is_forecast = false)
- CREATE INDEX idx_facility_scada_grouping ON public.facility_scada USING btree (network_id, facility_code, energy)

### Sample Data

| network\_id | interval | facility\_code | generated | energy | is\_forecast | energy\_quality\_flag |
| --- | --- | --- | --- | --- | --- | --- |
| NEM | 2014\-08\-24 08:05:00 | ROWALLAN | 9\.1945 | 0\.76206666666666666667 | False | 2 |
| NEM | 2013\-09\-17 11:40:00 | YWPS2 | 0\.0 | 0E\-20 | False | 2 |
| NEM | 2013\-06\-12 20:30:00 | LKBONNY2 | 53\.74159 | 4\.4579862500000000 | False | 2 |
| NEM | 2013\-07\-10 18:55:00 | CG4 | 0\.0 | 0E\-20 | False | 2 |
| NEM | 2016\-02\-19 05:55:00 | QPS5 | 0\.0 | 0E\-20 | False | 2 |

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
| commissioning | Commissioning |
| committed | Committed |
| construction | Construction |
| operating | Operating |
| emerging | Emerging |

## Table: public.feedback

Total rows: 126

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
| 9 | Bango facility feedback | 
\*\*Path:\*\*
/facility/au/NEM/BANGOWF/?range=7d&interval=30m

\*\*Sources:\*\*
https://aemo\.com\.au

\*\*Fields:\*\*
\[
 \{
  "key": " label",
  "value": ""
 \},
 \{
  "key": "BANGOWF1 label",
  "value": "BANGOWF1"
\.\.\. | steven@me\.com | None | 101\.173\.163\.18 | Mozilla/5\.0 \(Macintosh; Intel Mac OS X 10\_15\_7\) AppleWebKit/537\.36 \(KHTML, like Gecko\) Chrome/91\.0\.4472\.77 Safari/537\.36 | 2021\-06\-04 05:31:06\.394107\+00:00 | True |
| 84 | Flyers Creek Wind Farm facility feedback | 
\*\*No email provided\.\*\*
   

\*\*Path:\*\*
/facility/au/NEM/FLYCRKWF/?range=30d&interval=1d

\*\*Sources:\*\*
Registered Cap

\*\*Fields:\*\*

\`\`\`
\[
 \{
  "key": "FLYCRKWF reg cap",
  "value": 3\.8
 \}
\]
\`\`\`

\*\*Desc\.\.\. | None | None | 172\.19\.0\.1 | Mozilla/5\.0 \(Windows NT 10\.0; Win64; x64\) AppleWebKit/537\.36 \(KHTML, like Gecko\) Chrome/121\.0\.0\.0 Safari/537\.36 Edg/121\.0\.0\.0 | 2024\-02\-21 01:08:41\.438340\+00:00 | False |
| 111 | Port Stanvac facility feedback | 
\*\*No email provided\.\*\*
   

\*\*Path:\*\*
/facility/au/NEM/STANVAC/?range=all&interval=1M

\*\*Sources:\*\*
Yourself

\*\*Fields:\*\*

\`\`\`
\[
 \{
  "key": "STANV1 label",
  "value": "STANV1"
 \},
 \{
  "key": "STANV\.\.\. | None | None | 10\.244\.1\.28 | Mozilla/5\.0 \(Windows NT 10\.0; Win64; x64\) AppleWebKit/537\.36 \(KHTML, like Gecko\) Chrome/128\.0\.0\.0 Safari/537\.36 Edg/128\.0\.0\.0 | 2024\-09\-02 22:53:36\.977403\+00:00 | False |
| 25 | Bango facility feedback | 
\*\*No email provided\.\*\*
   

\*\*Path:\*\*
/facility/au/NEM/BANGOWF/?range=7d&interval=30m

\*\*Sources:\*\*
sdf

\*\*Fields:\*\*

\`\`\`
\[\]
\`\`\`

\*\*Description:\*\*
sdf
 | None | None | 61\.68\.241\.134 | Mozilla/5\.0 \(Macintosh; Intel Mac OS X 10\_15\_7\) AppleWebKit/537\.36 \(KHTML, like Gecko\) Chrome/91\.0\.4472\.124 Safari/537\.36 | 2021\-07\-03 05:44:37\.441475\+00:00 | True |
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
| None | 2020\-12\-09 01:46:29\.087850\+00:00 | 2022\-10\-04 06:24:38\.617043\+00:00 | bioenergy\_biogas | Biogas | True | bioenergy |
| None | 2020\-12\-09 01:46:29\.376830\+00:00 | 2022\-10\-04 06:24:38\.865319\+00:00 | gas\_ccgt | Gas \(CCGT\) | False | gas |
| None | 2024\-11\-08 07:36:59\.022442\+00:00 | None | battery | Battery | True | None |
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
| None | 2022\-10\-04 06:24:38\.411012\+00:00 | None | bioenergy | Bioenergy | \#A3886F | False |
| None | 2022\-10\-04 06:24:38\.313712\+00:00 | 2024\-11\-08 07:35:33\.398075\+00:00 | hydro | Hyrdo | \#4582B4 | True |
| None | 2022\-10\-04 06:24:38\.054393\+00:00 | None | gas | Gas | \#FF8813 | False |
| None | 2022\-10\-04 06:24:38\.013420\+00:00 | None | coal | Coal | \#4a4a4a | False |
| None | 2022\-10\-04 06:24:38\.214596\+00:00 | 2024\-11\-08 07:35:33\.398075\+00:00 | battery\_charging | Battery \(Charging\) | \#B2DAEF | True |

## Table: public.milestones

Total rows: 0

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| record_id | text | N/A | No |
| interval | timestamp without time zone | N/A | No |
| instance_id | uuid | N/A | No |
| aggregate | character varying | N/A | No |
| metric | character varying | N/A | Yes |
| period | character varying | N/A | Yes |
| significance | integer | N/A | No |
| value | double precision | N/A | No |
| value_unit | character varying | N/A | Yes |
| network_id | text | N/A | Yes |
| network_region | text | N/A | Yes |
| fueltech_id | text | N/A | Yes |
| description | character varying | N/A | Yes |
| description_long | character varying | N/A | Yes |
| previous_instance_id | uuid | N/A | Yes |
| created_at | timestamp without time zone | N/A | No |

### Create Table Statement

```sql
CREATE TABLE public.milestones
(
    record_id text NOT NULL,
    "interval" timestamp without time zone NOT NULL,
    instance_id uuid NOT NULL,
    aggregate character varying NOT NULL,
    metric character varying,
    period character varying,
    significance integer NOT NULL,
    value double precision NOT NULL,
    value_unit character varying,
    network_id text,
    network_region text,
    fueltech_id text,
    description character varying,
    description_long character varying,
    previous_instance_id uuid,
    created_at timestamp without time zone NOT NULL
);

```

### Constraints

- PRIMARY KEY (record_id, "interval")
- FOREIGN KEY (network_id) REFERENCES network(code)

### Indexes

- CREATE UNIQUE INDEX excl_milestone_record_id_interval ON public.milestones USING btree (record_id, "interval")
- CREATE INDEX idx_milestone_fueltech_id ON public.milestones USING btree (fueltech_id)
- CREATE INDEX idx_milestone_network_id ON public.milestones USING btree (network_id)
- CREATE INDEX ix_milestones_interval ON public.milestones USING btree ("interval")
- CREATE INDEX ix_milestones_record_id ON public.milestones USING btree (record_id)

## Table: public.network

Total rows: 6

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
| None | 2020\-12\-09 01:46:31\.176786\+00:00 | 2024\-11\-06 19:15:23\.412803\+00:00 | APVI | au | APVI | Australia/Perth | 15 | 600 | AWST | False | 0 | WEM | 2015\-03\-19 20:15:00\+00:00 | 2024\-11\-06 19:00:00\+00:00 |
| None | 2020\-12\-09 01:46:31\.118850\+00:00 | 2024\-11\-06 04:15:23\.483536\+00:00 | WEM | au | WEM | Australia/Perth | 30 | 480 | AWST | True | 0 | WEM | 2006\-09\-19 16:00:00\+00:00 | 2024\-11\-05 23:55:00\+00:00 |
| None | 2020\-12\-09 01:46:31\.057929\+00:00 | 2024\-11\-06 19:15:23\.412803\+00:00 | NEM | au | NEM | Australia/Sydney | 5 | 600 | AEST | True | 5 | NEM | 1998\-12\-06 15:40:00\+00:00 | 2024\-11\-06 19:15:00\+00:00 |
| None | 2023\-02\-22 09:54:49\.679305\+00:00 | 2023\-03\-17 22:55:36\.593610\+00:00 | OPENNEM\_ROOFTOP\_BACKFILL | au | OpenNEM Rooftop Backfill | Australia/Sydney | 30 | 600 | AEST | False | 0 | NEM | 2015\-03\-19 20:15:00\+00:00 | 2018\-02\-28 09:30:00\+00:00 |
| None | 2021\-04\-09 10:15:56\.408641\+00:00 | 2024\-11\-06 19:15:23\.412803\+00:00 | AEMO\_ROOFTOP | au | AEMO Rooftop | Australia/Sydney | 30 | 600 | AEST | False | 0 | NEM | 2016\-07\-31 14:30:00\+00:00 | 2024\-11\-06 18:00:00\+00:00 |

## Table: public.network_region

Total rows: 11

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
| None | 2020\-12\-09 01:46:31\.480819\+00:00 | None | NEM | TAS1 | None | None | None | True |
| None | 2021\-04\-09 10:15:56\.445329\+00:00 | None | AEMO\_ROOFTOP | TAS1 | None | None | None | True |
| None | 2020\-12\-09 01:46:31\.302424\+00:00 | None | NEM | NSW1 | None | None | None | True |
| None | 2020\-12\-09 01:46:31\.363840\+00:00 | None | NEM | QLD1 | None | None | None | True |
| None | 2021\-04\-09 10:15:56\.449008\+00:00 | None | AEMO\_ROOFTOP | SA1 | None | None | None | True |

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
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 1926\-09\-01 00:00:00\+00:00 | au | CPI | 2\.9 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 2000\-12\-31 00:00:00\+00:00 | au | CPI | 73\.1 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 1970\-09\-30 00:00:00\+00:00 | au | CPI | 9\.8 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 1975\-06\-30 00:00:00\+00:00 | au | CPI | 15\.8 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 1952\-09\-01 00:00:00\+00:00 | au | CPI | 6\.2 |

## Table: public.units

Total rows: 856

### Fields

| Field Name | Data Type | Max Length | Nullable |
|------------|-----------|------------|----------|
| id | integer | N/A | No |
| fueltech_id | text | N/A | Yes |
| status_id | text | N/A | Yes |
| station_id | integer | N/A | Yes |
| code | text | N/A | No |
| capacity_registered | numeric | N/A | Yes |
| registered | timestamp without time zone | N/A | Yes |
| deregistered | timestamp without time zone | N/A | Yes |
| unit_id | integer | N/A | Yes |
| unit_number | integer | N/A | Yes |
| unit_alias | text | N/A | Yes |
| unit_capacity | numeric | N/A | Yes |
| approved | boolean | N/A | No |
| emissions_factor_co2 | numeric | N/A | Yes |
| interconnector | boolean | N/A | No |
| interconnector_region_to | text | N/A | Yes |
| data_first_seen | timestamp with time zone | N/A | Yes |
| data_last_seen | timestamp with time zone | N/A | Yes |
| expected_closure_date | timestamp without time zone | N/A | Yes |
| expected_closure_year | integer | N/A | Yes |
| interconnector_region_from | text | N/A | Yes |
| emission_factor_source | text | N/A | Yes |
| dispatch_type | text | N/A | No |

### Create Table Statement

```sql
CREATE TABLE public.units
(
    id integer NOT NULL,
    fueltech_id text,
    status_id text,
    station_id integer,
    code text NOT NULL,
    capacity_registered numeric,
    registered timestamp without time zone,
    deregistered timestamp without time zone,
    unit_id integer,
    unit_number integer,
    unit_alias text,
    unit_capacity numeric,
    approved boolean NOT NULL,
    emissions_factor_co2 numeric,
    interconnector boolean NOT NULL,
    interconnector_region_to text,
    data_first_seen timestamp with time zone,
    data_last_seen timestamp with time zone,
    expected_closure_date timestamp without time zone,
    expected_closure_year integer,
    interconnector_region_from text,
    emission_factor_source text,
    dispatch_type text NOT NULL
);

```

### Constraints

- PRIMARY KEY (id)
- FOREIGN KEY (fueltech_id) REFERENCES fueltech(code)
- FOREIGN KEY (status_id) REFERENCES facility_status(code)
- FOREIGN KEY (station_id) REFERENCES facilities(id)

### Indexes

- CREATE UNIQUE INDEX facility_pkey ON public.units USING btree (id)
- CREATE INDEX idx_facility_fueltech_id ON public.units USING btree (fueltech_id)
- CREATE UNIQUE INDEX ix_units_code ON public.units USING btree (code)
- CREATE INDEX ix_units_data_first_seen ON public.units USING btree (data_first_seen)
- CREATE INDEX ix_units_data_last_seen ON public.units USING btree (data_last_seen)
- CREATE INDEX ix_units_interconnector ON public.units USING btree (interconnector)
- CREATE INDEX ix_units_interconnector_region_from ON public.units USING btree (interconnector_region_from)
- CREATE INDEX ix_units_interconnector_region_to ON public.units USING btree (interconnector_region_to)
- CREATE INDEX idx_facility_station_id ON public.units USING btree (station_id)
- CREATE INDEX idx_units_lookup ON public.units USING btree (code, fueltech_id) WHERE ((fueltech_id IS NOT NULL) AND (fueltech_id <> ALL (ARRAY['imports'::text, 'exports'::text, 'interconnector'::text])))

### Sample Data

| id | fueltech\_id | status\_id | station\_id | code | capacity\_registered | registered | deregistered | unit\_id | unit\_number | unit\_alias | unit\_capacity | approved | emissions\_factor\_co2 | interconnector | interconnector\_region\_to | data\_first\_seen | data\_last\_seen | expected\_closure\_date | expected\_closure\_year | interconnector\_region\_from | emission\_factor\_source | dispatch\_type |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 795 | wind | operating | 553 | RYEPARK1 | 396\.0 | None | None | None | None | None | None | True | 0\.0 | False | None | 2023\-08\-18 09:40:00\+00:00 | 2024\-11\-15 08:00:00\+00:00 | None | None | None | None | GENERATOR |
| 572 | gas\_ocgt | operating | 409 | PINJAR\_GT3 | 39\.2999999999999971578290569595992565155029296875 | 2003\-07\-01 00:00:00 | None | None | None | None | None | True | 0\.81999999999999995115018691649311222136020660400390625 | False | None | 2013\-12\-21 17:30:00\+00:00 | 2024\-09\-21 16:20:00\+00:00 | None | None | None | None | GENERATOR |
| 852 | battery | operating | 101 | DALNTH1 | 30 | 2024\-07\-24 00:00:00 | None | None | None | None | None | True | None | False | None | None | None | 2030\-01\-01 00:00:00 | None | None | None | BIDIRECTIONAL |
| 64 | gas\_steam | retired | 46 | BELLBAY1 | 120\.0 | None | None | None | None | None | None | True | 0\.70860000000000000763833440942107699811458587646484375 | False | None | 2005\-05\-16 13:35:00\+00:00 | 2008\-11\-19 08:05:00\+00:00 | None | None | None | None | GENERATOR |
| 754 | None | operating | 508 | V\-SA\-2 | None | None | None | None | None | None | None | False | 0\.0 | False | None | 2009\-07\-01 00:05:00\+00:00 | 2020\-12\-31 12:15:00\+00:00 | None | None | None | None | GENERATOR |
