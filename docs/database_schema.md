# Database Schema

Database: opennem
PostgreSQL version: PostgreSQL 17.0 (Ubuntu 17.0-1.pgdg24.04+1) on x86_64-pc-linux-gnu, compiled by gcc (Ubuntu 13.2.0-23ubuntu4) 13.2.0, 64-bit
Schemas: public

## Table of Contents

| Schema | Table Name | Row Count |
|--------|------------|----------|
| public | [aemo_market_notices](#public-aemo-market-notices) | 0 |
| public | [alembic_version](#public-alembic-version) | 1 |
| public | [at_network_demand](#public-at-network-demand) | 63,418 |
| public | [at_network_flows](#public-at-network-flows) | 8,055,675 |
| public | [balancing_summary](#public-balancing-summary) | 11,410,419 |
| public | [bom_observation](#public-bom-observation) | 5,955,940 |
| public | [bom_station](#public-bom-station) | 773 |
| public | [crawl_history](#public-crawl-history) | 350,874 |
| public | [crawl_meta](#public-crawl-meta) | 51 |
| public | [facilities](#public-facilities) | 554 |
| public | [facility_scada](#public-facility-scada) | 780,869,387 |
| public | [facility_status](#public-facility-status) | 12 |
| public | [feedback](#public-feedback) | 126 |
| public | [fueltech](#public-fueltech) | 26 |
| public | [fueltech_group](#public-fueltech-group) | 10 |
| public | [milestones](#public-milestones) | 0 |
| public | [network](#public-network) | 6 |
| public | [network_region](#public-network-region) | 11 |
| public | [stats](#public-stats) | 403 |
| public | [units](#public-units) | 844 |

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
| 7d6b0be0009e |

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
| 2008\-03\-15 00:00:00\+00:00 | NEM | SNOWY1 | 4\.56442666666666666661 | 61446\.0980750000000011833000 |
| 2024\-11\-02 00:00:00\+00:00 | NEM | SNOWY1 | None | None |
| 2004\-07\-22 00:00:00\+00:00 | NEM | TAS1 | None | None |
| 2022\-06\-13 00:00:00\+00:00 | NEM | VIC1 | 128\.64827474999999999994 | 105041575\.6720490308333061530929000 |
| 2014\-12\-02 00:00:00\+00:00 | NEM | VIC1 | 133\.96009733333333333332 | 4843049\.9483516616666666640370000 |

## Table: public.at_network_flows

Total rows: 8,055,675

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
| 2010\-05\-19 12:20:00\+00:00 | NEM | NSW1 | 87\.25 | 46\.666666666666664 | 74\.1853183743663 | 42\.519923752579565 | 0\.0 | 0\.0 |
| 2012\-05\-28 20:15:00\+00:00 | NEM | TAS1 | 11\.416666666666666 | 0\.0 | 14\.783361773806252 | 0\.0 | 0\.0 | 0\.0 |
| 2014\-04\-06 07:25:00\+00:00 | NEM | NSW1 | 72\.015495 | 0\.0 | 77\.81080614825234 | 0\.0 | 0\.0 | 0\.0 |
| 2020\-03\-13 20:50:00\+00:00 | NEM | VIC1 | 17\.4722825 | 54\.3150225 | 1\.5419496173430653 | 49\.56581180969377 | 0\.0 | 0\.0 |
| 2020\-11\-16 02:15:00\+00:00 | NEM | VIC1 | 40\.14232166666667 | 108\.4159825 | 6\.094114882861839 | 77\.65719366994531 | 0\.0 | 0\.0 |

## Table: public.balancing_summary

Total rows: 11,410,419

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

- CREATE INDEX idx_balancing_summary_interval_network_region ON public.balancing_summary USING btree ("interval" DESC, network_id, network_region)
- CREATE INDEX ix_balancing_summary_network_region ON public.balancing_summary USING btree (network_region)
- CREATE UNIQUE INDEX pk_balancing_summary_pkey ON public.balancing_summary USING btree ("interval", network_id, network_region, is_forecast)
- CREATE INDEX ix_balancing_summary_interval ON public.balancing_summary USING btree ("interval")

### Sample Data

| interval | network\_id | network\_region | forecast\_load | generation\_scheduled | generation\_non\_scheduled | generation\_total | price | is\_forecast | net\_interchange | demand\_total | price\_dispatch | net\_interchange\_trading | demand |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2017\-10\-12 02:20:00 | NEM | TAS1 | None | None | None | None | None | False | 395\.78 | 1116\.582670 | 14\.81376 | None | 902\.29 |
| 2009\-03\-16 23:50:00 | NEM | NSW1 | None | None | None | None | None | False | 290\.15 | 9852\.38 | None | None | 9834\.9 |
| 2022\-01\-05 13:25:00 | NEM | NSW1 | None | None | None | None | 75\.87 | False | 196\.93 | 7872\.528420 | 75\.86563 | None | 7762\.46 |
| 2014\-04\-18 04:50:00 | NEM | VIC1 | None | None | None | None | None | False | 1041\.72 | 4026\.128 | 33\.65837 | None | 3832\.34 |
| 2021\-03\-25 05:50:00 | NEM | TAS1 | None | None | None | None | None | False | 144\.61 | 1024\.6546 | 19\.74427 | None | 926\.79 |

## Table: public.bom_observation

Total rows: 5,955,940

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
| 2013\-12\-14 07:00:00\+00:00 | 066214 | 19\.4 | 21\.4 | None | None | None | None | None | 20\.9 | None | None | None |
| 2021\-04\-26 18:30:00\+00:00 | 074258 | 1\.1 | 4\.6 | 1025\.9 | WSW | 11 |  |  | 94 | 13 | None | None |
| 2021\-04\-02 10:00:00\+00:00 | 084142 | 14\.5 | 15\.3 | 1027\.4 | N | 2 |  |  | 63 | 6 | None | None |
| 2021\-02\-26 02:00:00\+00:00 | 065070 | 29\.0 | 28\.6 | 1011\.0 | W | 9 |  |  | 47 | 19 | None | None |
| 2023\-03\-22 09:30:00\+00:00 | 009021 | 23\.6 | 27\.0 | 1011\.2 | SW | 28\.0 | None | None | 50\.0 | 35\.0 | None | None |

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
| 009937 | WA | BUSSELTON JETTY | None | 0101000020E6100000F6285C8FC2D55C40713D0AD7A3D040C0 | http://www\.bom\.gov\.au/fwo/IDW60801/IDW60801\.95602\.json | False | Busselton Jetty | 5 | http://www\.bom\.gov\.au/products/IDW60801/IDW60801\.95602\.shtml | 3 | None |
| 010568 | WA | HYDEN | None | 0101000020E61000009A99999999B95D40B81E85EB513840C0 | http://www\.bom\.gov\.au/fwo/IDW60801/IDW60801\.95627\.json | False | Hyden | 5 | http://www\.bom\.gov\.au/products/IDW60801/IDW60801\.95627\.shtml | 299 | None |
| 074037 | NSW | YANCO AGRICULTURAL INSTITUTE | None | 0101000020E6100000F6285C8FC24D62408FC2F5285C4F41C0 | http://www\.bom\.gov\.au/fwo/IDN60801/IDN60801\.95705\.json | False | Yanco | 5 | http://www\.bom\.gov\.au/products/IDN60801/IDN60801\.95705\.shtml | 164 | None |
| 058214 | NSW | LISMORE AIRPORT AWS | None | 0101000020E6100000B81E85EB5128634014AE47E17AD43CC0 | http://www\.bom\.gov\.au/fwo/IDN60801/IDN60801\.94572\.json | False | Lismore Airport | 5 | http://www\.bom\.gov\.au/products/IDN60801/IDN60801\.94572\.shtml | 9 | None |
| 039104 | QLD | MONTO TOWNSHIP | None | 0101000020E6100000A4703D0AD7E362405C8FC2F528DC38C0 | http://www\.bom\.gov\.au/fwo/IDQ60801/IDQ60801\.94377\.json | False | Monto Township | 5 | http://www\.bom\.gov\.au/products/IDQ60801/IDQ60801\.94377\.shtml | 239 | None |

## Table: public.crawl_history

Total rows: 350,874

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
| nemweb | au\.nemweb\.current\.dispatch\_scada | NEM | 2024\-08\-14 08:05:00\+00:00 | 468 | None | 2024\-08\-13 22:05:29\+00:00 |
| nemweb | au\.nemweb\.current\.dispatch\_scada | NEM | 2023\-12\-10 19:10:00\+00:00 | 454 | None | 2023\-12\-10 09:10:09\+00:00 |
| nemweb | au\.nemweb\.current\.dispatch\_is | NEM | 2024\-04\-04 08:55:00\+00:00 | 16 | None | 2024\-04\-03 22:55:01\+00:00 |
| nemweb | au\.nemweb\.current\.dispatch\_is | NEM | 2024\-02\-07 03:35:00\+00:00 | 16 | None | 2024\-02\-06 17:35:00\+00:00 |
| nemweb | au\.nemweb\.current\.trading\_is | NEM | 2023\-11\-08 17:30:00\+00:00 | 5 | None | 2023\-11\-08 07:30:06\+00:00 |

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
| au\.nem\.current\.dispatch\_is | \{'version': '2', 'last\_crawled': '2022\-06\-27T11:21:11\+10:00', 'server\_latest': '2022\-06\-27T11:25:00\+10:00', 'latest\_processed': '2022\-06\-27T11:25:00\+10:00'\} | 2022\-06\-10 07:17:17\.371397\+00:00 | 2022\-06\-27 01:25:10\.485255\+00:00 |
| au\.nemweb\.current\.dispatch\_scada | \{'version': '2', 'last\_crawled': '2024\-11\-08T17:45:30\+11:00', 'server\_latest': '2024\-11\-07T05:25:00\+10:00', 'latest\_processed': '2024\-11\-07T05:25:00\+10:00'\} | 2023\-09\-04 10:45:41\.825330\+00:00 | 2024\-11\-08 06:45:30\.748665\+00:00 |
| au\.mms\.trading\_price | \{'version': '2', 'last\_crawled': '2022\-10\-25T07:54:10\+11:00'\} | 2022\-10\-24 20:54:10\.779819\+00:00 | 2022\-10\-24 20:54:10\.968785\+00:00 |
| apvi\.all\.data | \{'version': '2', 'last\_crawled': '2023\-09\-01T12:46:11\+10:00'\} | 2022\-11\-03 08:59:56\.244007\+00:00 | 2023\-09\-01 02:46:11\.323592\+00:00 |
| au\.nemweb\.archive\.dispatch\_actual\_gen | \{'version': '2', 'last\_crawled': '2024\-09\-09T16:38:47\+10:00'\} | 2022\-07\-21 02:19:10\.279228\+00:00 | 2024\-09\-09 06:38:47\.768350\+00:00 |

## Table: public.facilities

Total rows: 554

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
| 55 | BOCOROCK | Boco Rock | None | https://en\.wikipedia\.org/wiki/Boco\_Rock\_Wind\_Farm | Q68781022 | NEM | NSW1 | True | https://www\.bocorockwindfarm\.com\.au/ |
| 345 | WPWF | Wattle Point | Wattle Point Wind Farm is a wind farm near Edithburgh on the Yorke Peninsula in South Australia, which has been operating since April 2005\. When it was officially opened in June of that year it was Au\.\.\. | https://en\.wikipedia\.org/wiki/Wattle\_Point\_Wind\_Farm | Q7974989 | NEM | SA1 | True | https://www\.agl\.com\.au/about\-agl/how\-we\-source\-energy/wattle\-point\-wind\-farm |
| 363 | CALL\_A | Callide A | Callide Power Station is located near Biloela, in Central Queensland, Australia\. It is coal powered with eight steam turbines with a combined generation capacity of 1,720 MW of electricity\. Callide A \.\.\. | https://en\.wikipedia\.org/wiki/Callide\_Power\_Station | Q2944656 | NEM | QLD1 | True | None |
| 448 | NEM\_FLOW\_VIC1 | Flows for NEM state VIC | None | None | None | NEM | VIC1 | False | None |
| 293 | TABMILL2 | Tableland Mill | None | None | None | NEM | QLD1 | True | https://www\.msfsugar\.com\.au/tableland\-green\-energy\-power\-plant/ |

## Table: public.facility_scada

Total rows: 780,869,387

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
| eoi_quantity | numeric | N/A | Yes |

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
    energy_quality_flag numeric NOT NULL,
    eoi_quantity numeric
);

```

### Indexes

- CREATE INDEX ix_facility_scada_facility_code ON public.facility_scada USING btree (facility_code)
- CREATE INDEX ix_facility_scada_interval ON public.facility_scada USING btree ("interval")
- CREATE INDEX ix_facility_scada_network_id ON public.facility_scada USING btree (network_id)

### Sample Data

| network\_id | interval | facility\_code | generated | energy | is\_forecast | energy\_quality\_flag | eoi\_quantity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NEM | 2010\-02\-09 01:40:00 | REDBANK1 | 141\.0 | None | False | 0 | None |
| NEM | 2002\-02\-10 10:25:00 | GSTONE5 | 195\.82 | 89\.08166666666665 | False | 0 | None |
| WEM | 2013\-04\-08 16:00:00 | NEWGEN\_KWINANA\_CCG1 | None | 154\.065 | False | 0 | None |
| NEM | 2006\-10\-07 12:30:00 | KAREEYA1 | 19\.34 | None | False | 0 | None |
| NEM | 2007\-09\-25 07:25:00 | STAN\-3 | 319\.60001 | 180\.63333291666663 | False | 0 | None |

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
| shelved | Shelved |
| mothballed | Mothballed |
| operating | Operating |
| committed | Committed |
| announced | Announced |

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
| 57 | test | test | test@test\.com | None | None | None | 2023\-05\-22 03:39:45\.924830\+00:00 | False |
| 131 | Chinchilla facility feedback | 
\*\*No email provided\.\*\*
   

\*\*Path:\*\*
/facility/au/NEM/CHBESS/?range=1d&interval=30m

\*\*Sources:\*\*
?

\*\*Fields:\*\*

\`\`\`
\[
 \{
  "key": "Facility fuel tech",
  "value": \[
   \{
    "id": "battery\_chargin\.\.\. | None | None | 10\.244\.84\.89 | Mozilla/5\.0 \(Linux; Android 10; K\) AppleWebKit/537\.36 \(KHTML, like Gecko\) SamsungBrowser/26\.0 Chrome/122\.0\.0\.0 Mobile Safari/537\.36 | 2024\-11\-04 21:07:15\.177006\+00:00 | False |
| 20 | Bairnsdale facility feedback | 
\*\*Path:\*\*
/facility/au/NEM/DEIBDL/?range=7d&interval=30m

\*\*Sources:\*\*
test

\*\*Fields:\*\*

\`\`\`
\[
 \{
  "key": "Facility status and dates",
  "value": "operating since  9 May 2001"
 \}
\]
\`\`\`

\*\*Descripti\.\.\. | None | None | 61\.68\.241\.134 | Mozilla/5\.0 \(Macintosh; Intel Mac OS X 10\_15\_7\) AppleWebKit/537\.36 \(KHTML, like Gecko\) Chrome/91\.0\.4472\.124 Safari/537\.36 | 2021\-07\-03 04:21:57\.920806\+00:00 | True |
| 27 | Bango facility feedback | 
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
sdfsd
 | None | None | 61\.68\.241\.134 | Mozilla/5\.0 \(Macintosh; Intel Mac OS X 10\_15\_7\) AppleWebKit/537\.36 \(KHTML, like Gecko\) Chrome/91\.0\.4472\.124 Safari/537\.36 | 2021\-07\-03 05:48:25\.027999\+00:00 | True |
| 113 | Stockyard Hill facility feedback | 
\*\*No email provided\.\*\*
   

\*\*Path:\*\*
/facility/au/NEM/STOCKYD/?range=1y&interval=1w

\*\*Sources:\*\*
Literally yourself

\*\*Fields:\*\*

\`\`\`
\[
 \{
  "key": "STOCKYD1 reg cap",
  "value": 456\.96
 \}
\]
\`\`\`

\*\.\.\. | None | None | 10\.244\.1\.28 | Mozilla/5\.0 \(Windows NT 10\.0; Win64; x64\) AppleWebKit/537\.36 \(KHTML, like Gecko\) Chrome/128\.0\.0\.0 Safari/537\.36 Edg/128\.0\.0\.0 | 2024\-09\-07 14:28:32\.853525\+00:00 | False |

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
| None | 2020\-12\-09 01:46:29\.904852\+00:00 | 2022\-10\-04 06:24:39\.329845\+00:00 | solar\_rooftop | Solar \(Rooftop\) | True | solar |
| None | 2024\-11\-08 07:36:59\.022442\+00:00 | None | wind\_offshore | Offshore Wind | True | wind |
| None | 2020\-12\-09 01:46:30\.137845\+00:00 | 2022\-10\-04 06:24:39\.566146\+00:00 | nuclear | Nuclear | False | None |
| None | 2020\-12\-09 01:46:29\.552866\+00:00 | 2022\-10\-04 06:24:39\.023691\+00:00 | gas\_steam | Gas \(Steam\) | False | gas |
| None | 2020\-12\-09 01:46:29\.087850\+00:00 | 2022\-10\-04 06:24:38\.617043\+00:00 | bioenergy\_biogas | Biogas | True | bioenergy |

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
| None | 2022\-10\-04 06:24:38\.013420\+00:00 | None | coal | Coal | \#4a4a4a | False |
| None | 2022\-10\-04 06:24:38\.263261\+00:00 | 2024\-11\-08 07:35:33\.398075\+00:00 | battery\_discharging | Battery \(Discharging\) | \#00A2FA | True |
| None | 2022\-10\-04 06:24:38\.411012\+00:00 | None | bioenergy | Bioenergy | \#A3886F | False |
| None | 2022\-10\-04 06:24:38\.054393\+00:00 | None | gas | Gas | \#FF8813 | False |
| None | 2022\-10\-04 06:24:38\.114476\+00:00 | 2024\-11\-08 07:35:33\.398075\+00:00 | wind | Wind | \#417505 | True |

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
| None | 2023\-02\-22 09:54:49\.679305\+00:00 | 2023\-03\-17 22:55:36\.593610\+00:00 | OPENNEM\_ROOFTOP\_BACKFILL | au | OpenNEM Rooftop Backfill | Australia/Sydney | 30 | 600 | AEST | False | 0 | NEM | 2015\-03\-19 20:15:00\+00:00 | 2018\-02\-28 09:30:00\+00:00 |
| None | 2021\-04\-12 07:06:18\.835747\+00:00 | None | AEMO\_ROOFTOP\_BACKFILL | au | AEMO Rooftop Backfill | Australia/Sydney | 30 | 600 | AEST | False | 0 | NEM | None | None |
| None | 2021\-04\-09 10:15:56\.408641\+00:00 | 2024\-11\-06 19:15:23\.412803\+00:00 | AEMO\_ROOFTOP | au | AEMO Rooftop | Australia/Sydney | 30 | 600 | AEST | False | 0 | NEM | 2016\-07\-31 14:30:00\+00:00 | 2024\-11\-06 18:00:00\+00:00 |
| None | 2020\-12\-09 01:46:31\.176786\+00:00 | 2024\-11\-06 19:15:23\.412803\+00:00 | APVI | au | APVI | Australia/Perth | 15 | 600 | AWST | False | 0 | WEM | 2015\-03\-19 20:15:00\+00:00 | 2024\-11\-06 19:00:00\+00:00 |
| None | 2020\-12\-09 01:46:31\.118850\+00:00 | 2024\-11\-06 04:15:23\.483536\+00:00 | WEM | au | WEM | Australia/Perth | 30 | 480 | AWST | True | 0 | WEM | 2006\-09\-19 16:00:00\+00:00 | 2024\-11\-05 23:55:00\+00:00 |

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
| None | 2020\-12\-09 01:46:31\.239865\+00:00 | None | WEM | WEM | None | None | None | True |
| None | 2020\-12\-09 01:46:31\.363840\+00:00 | None | NEM | QLD1 | None | None | None | True |
| None | 2021\-04\-09 10:15:56\.445329\+00:00 | None | AEMO\_ROOFTOP | TAS1 | None | None | None | True |
| None | 2020\-12\-09 01:46:31\.480819\+00:00 | None | NEM | TAS1 | None | None | None | True |
| None | 2020\-12\-09 01:46:31\.540863\+00:00 | None | NEM | SA1 | None | None | None | True |

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
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 1994\-09\-30 00:00:00\+00:00 | au | CPI | 62\.3 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 1987\-06\-30 00:00:00\+00:00 | au | CPI | 46\.0 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 2012\-12\-31 00:00:00\+00:00 | au | CPI | 102\.0 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 2011\-09\-30 00:00:00\+00:00 | au | CPI | 99\.8 |
| None | 2021\-01\-05 09:47:54\.294658\+00:00 | None | 1979\-03\-31 00:00:00\+00:00 | au | CPI | 23\.0 |

## Table: public.units

Total rows: 844

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

### Sample Data

| id | fueltech\_id | status\_id | station\_id | code | capacity\_registered | registered | deregistered | unit\_id | unit\_number | unit\_alias | unit\_capacity | approved | emissions\_factor\_co2 | interconnector | interconnector\_region\_to | data\_first\_seen | data\_last\_seen | expected\_closure\_date | expected\_closure\_year | interconnector\_region\_from | emission\_factor\_source | dispatch\_type |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 83 | solar\_utility | operating | 62 | BROKENH1 | 53 | None | None | None | None | None | None | True | 0\.0 | False | None | 2015\-09\-15 00:55:00\+00:00 | 2024\-11\-06 08:35:00\+00:00 | None | None | None | None | GENERATOR |
| 816 | wind | committed | 567 | CLRKCWF1 | 346\.5 | None | None | None | None | None | None | True | None | False | None | None | None | 2049\-01\-01 00:00:00 | None | None | None | GENERATOR |
| 428 | gas\_steam | retired | 311 | TORRA2 | 120\.0 | None | None | None | None | None | None | True | 0\.70860000000000000763833440942107699811458587646484375 | False | None | 1998\-12\-06 19:55:00\+00:00 | 2020\-03\-20 14:40:00\+00:00 | None | None | None | None | GENERATOR |
| 800 | solar\_utility | operating | 488 | ADPPV3 | 0\.0200000000000000004163336342344337026588618755340576171875 | None | None | None | 1 | None | 6\.27 | True | 0\.0 | False | None | None | None | None | None | None | None | GENERATOR |
| 222 | gas\_ocgt | operating | 162 | JLA03 | 51\.0 | None | None | None | None | None | None | True | 0\.879399999999999959499064061674289405345916748046875 | False | None | 1998\-12\-10 01:25:00\+00:00 | 2024\-10\-15 09:20:00\+00:00 | None | None | None | None | GENERATOR |
