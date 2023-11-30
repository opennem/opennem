"""
Module that takes a natural language query and asks OpenAPI for a sql statement
in return
"""
import logging
import sys
from pathlib import Path
from textwrap import dedent

from openai import OpenAI

from opennem import settings
from opennem.recordreactor.ai.train import generate_prompt_set
from opennem.recordreactor.ai.utils import (
    BadQuery,
    NotReadOnlyException,
    OpennemResultSet,
    is_read_only_query,
    run_opennem_query,
)

logger = logging.getLogger("opennem.recordreactor.ai")


SYSTEM_PROMPT = """You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct postgresql query to run, then look at the results of the query and return the answer.
Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most {limit} results.
You can order the results by a relevant column to return the most interesting examples in the database.
Never query for all the columns from a specific table, only ask for a the few relevant columns given the question.
DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.
You will only return the sql query **and nothing more**
"""

USER_PROMPT = """###
Postgres database with the following table definitions:
----------
CREATE TABLE at_facility_daily (
    trading_day timestamp with time zone NOT NULL,
    network_id text NOT NULL,
    facility_code text NOT NULL,
    fueltech_id text,
    energy numeric,
    market_value numeric,
    emissions numeric
)
/*
3 rows from facility_scada table:
created_by	created_at	updated_at	network_id	trading_interval	facility_code	generated	eoi_quantity	is_forecast	energy_quality_flag
au.nem.archive.dispatch	2020-12-09 03:08:53.167647+00:00	None	NEM	2020-11-11 18:05:00+00:00	BBTHREE2	-1.0	None	False	0
au.nem.archive.dispatch	2020-12-09 03:08:53.167647+00:00	None	NEM	2020-11-11 18:05:00+00:00	BBTHREE3	-1.05	None	False	0
au.nem.archive.dispatch	2020-12-09 03:08:53.167647+00:00	None	NEM	2020-11-11 18:05:00+00:00	BDL01	0.0	None	False	0
*/
CREATE TABLE balancing_summary (
    trading_interval timestamp with time zone NOT NULL,
    network_id text NOT NULL,
    forecast_load numeric,
    generation_scheduled numeric,
    generation_non_scheduled numeric,
    generation_total numeric,
    price numeric,
    network_region text NOT NULL,
    is_forecast boolean,
    net_interchange numeric,
    demand_total numeric,
    price_dispatch numeric,
    net_interchange_trading numeric,
    demand numeric
)
CREATE TABLE facility (
    network_id text NOT NULL,
    fueltech_id text,
    status_id text,
    station_id integer,
    code text NOT NULL,
    network_code text,
    network_region text,
    network_name text,
    capacity_registered numeric,
    registered timestamp without time zone,
    deregistered timestamp without time zone,
    emissions_factor_co2 numeric,
    interconnector boolean,
    interconnector_region_to text,
    interconnector_region_from text,
    data_first_seen timestamp with time zone,
    data_last_seen timestamp with time zone,
    expected_closure_date timestamp without time zone,
    expected_closure_year integer,
    emission_factor_source text
)
CREATE TABLE facility_scada (
    network_id text NOT NULL,
    trading_interval timestamp with time zone NOT NULL,
    facility_code text NOT NULL,
    generated numeric,
    eoi_quantity numeric,
    is_forecast boolean NOT NULL,
)
CREATE TABLE station (
    id integer NOT NULL,
    participant_id integer,
    location_id integer,
    code text NOT NULL,
    name text,
    description text,
    wikipedia_link text,
    wikidata_id text,
    website_url text
)
CREATE TABLE facility_status (
    code text NOT NULL,
    label text
)
CREATE TABLE fueltech (
    code text NOT NULL,
    label text,
    renewable boolean,
    fueltech_group_id text
)
CREATE TABLE fueltech_group (
    code text NOT NULL,
    label text
)
-----------
you can only query the defined table definitions.
network contains three records, NEM in Australia and WEM in Australia and APVI which stores solar rooftop data.
network_region network id is network code.
NEM has network regions which are Australian states:
    * New South Wales is code NSW1
    * Queensland is code QLD1
    * Victoria is code VIC1
    * South Australia is code SA1
    * Tasmania is code TAS1
WEM network has network regions:
    * Western Australia is code WEM
station name is the name of the power station.
facility_scada eoi_quantity is total energy and is updated every hour.
facility_status has possible statuses of:
    * operating
    * construction
    * decommissioned
    * retired
    * committed
    * announced
balancing_summary price is the power price in $/MWh.
balancing_summary price has a record every 30 minutes.
power station names can be looked up in the station name field and linked to a facility code using the facility code field.
fueltech_group has groups of fueltechs:
    * coal
    * gas
    * hydro
    * wind
    * solar
    * battery_charging
    * battery_discharging
    * pumps
    * distillate
DO NOT EXPLAIN THE QUERY.
DO NOT MODIFY THE DATABASE.
###
generate **only** an sql query that: {query}
"""

MESSAGES = [{"role": "system", "content": SYSTEM_PROMPT}]

ERROR_TEMPLATE = "Try again. " "The SQL query you just generated resulted in the following error message:\n" "{error_message}"

OPENNEM_PROMPTS = generate_prompt_set(Path(__file__).parent / "data" / "prompts.txt")

openai_client = OpenAI(
    # This is the default and can be omitted
    api_key=settings.openai_api_key,
)


def get_openai_chat_prompt(query: str, error_detail: list[dict] | None = None) -> str:
    """
    Function that takes a natural language query and asks OpenAI for a sql
    statement in return
    """

    system_prompt_formatted = SYSTEM_PROMPT.format(limit=100)

    messages = (
        [{"role": "system", "content": system_prompt_formatted}]
        + OPENNEM_PROMPTS
        + [{"role": "user", "content": USER_PROMPT.format(query=query)}]
    )

    if error_detail:
        # messages += error_detail
        logger.error("Error detail not yet supported")
        pass

    response = openai_client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=messages,
        temperature=0,
    )

    logger.info(response)

    if not response.choices:
        raise Exception("No result")

    if not response.choices[0].message.content:
        raise Exception("No result")

    response_content = response.choices[0].message.content

    return response_content


def run_human_query_with_retries(query: str, error_detail: list[dict] | None = None, retry_number: int = 0) -> OpennemResultSet:
    """Runs the query with retries"""

    if retry_number > 3:
        raise Exception("Too many retries")

    sql_query = get_openai_chat_prompt(query, error_detail=error_detail)

    try:
        results = run_opennem_query(sql_query)

    except BadQuery as e:
        logger.info("Bad query: %s", e)

        if not error_detail:
            error_detail = []

        error_detail.append({"role": "assistant", "content": sql_query})
        error_detail.append({"role": "user", "content": ERROR_TEMPLATE.format(error_message=str(e))})

        return run_human_query_with_retries(query, retry_number=retry_number + 1)

    if not results:
        raise Exception("No result")

    return results


def get_opennem_query_from_prompt(prompt: str) -> str:
    """Function that takes a natural language query and asks OpenAPI for a sql statement in return"""

    query = get_openai_chat_prompt(prompt)

    if not is_read_only_query(query):
        raise NotReadOnlyException("Only read-only queries are allowed.")

    logger.debug(dedent(query))

    query = query.lower()

    return query


if __name__ == "__main__":
    response = get_opennem_query_from_prompt(sys.argv[1])

    print(response)
