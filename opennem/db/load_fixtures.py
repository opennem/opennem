"""
Loads database fixtures that are required.

"""

import asyncio
import logging
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import and_, select

from opennem.core.loader import load_data
from opennem.db import SessionLocalAsync
from opennem.db.models.opennem import BomStation, FacilityStatus, FuelTech, FuelTechGroup, Network, NetworkRegion

logger = logging.getLogger("opennem.db.load_fixtures")


async def load_fueltechs() -> None:
    """
    Load the fueltechs and fueltech groups fixture
    """
    fueltech_groups = load_data("fueltech_groups.json", from_fixture=True)
    fueltechs = load_data("fueltechs.json", from_fixture=True)

    async with SessionLocalAsync() as session:
        for ftg in fueltech_groups:
            ftg_code = ftg.get("code")

            if not ftg_code:
                logger.error("Fueltech group has no code")
                continue

            fueltech_group_query = await session.scalars(select(FuelTechGroup).where(FuelTechGroup.code == ftg_code))
            fueltech_group = fueltech_group_query.one_or_none()

            logger.debug(f"Loaded fueltech group {fueltech_group.code}")

            if not fueltech_group:
                fueltech_group = FuelTechGroup(
                    code=ftg["code"],
                )

            fueltech_group.label = ftg.get("label")
            fueltech_group.color = ftg.get("color")
            fueltech_group.renewable = ftg.get("renewable", False)

            try:
                session.add(fueltech_group)
                await session.commit()
                logger.info(f"Loaded fueltech Group {fueltech_group.code}")
            except Exception:
                logger.error(f"Have fueltech group {fueltech_group.code}")
                await session.rollback()

        for ft in fueltechs:
            ft_code = ft.get("code")

            if not ft_code:
                logger.error("Fueltech has no code")
                continue

            fueltech = await session.scalars(select(FuelTech).where(FuelTech.code == ft_code))
            fueltech = fueltech.one_or_none()

            if not fueltech:
                fueltech = FuelTech(
                    code=ft_code,
                )

            fueltech.label = ft.get("label", "")
            fueltech.renewable = ft.get("renewable", False)
            fueltech.fueltech_group_id = ft.get("fueltech_group_id")

            try:
                session.add(fueltech)
                await session.commit()
                logger.info(f"Loaded fueltech {fueltech.code}")
            except Exception:
                logger.error(f"Have {fueltech.code}")
                await session.rollback()


async def load_facilitystatus() -> None:
    """
    Load the facility status fixture
    """
    fixture = load_data("facility_status.json", from_fixture=True)

    async with SessionLocalAsync() as session:
        for status in fixture:
            facility_status = await session.execute(select(FacilityStatus).filter_by(code=status["code"]))
            facility_status = facility_status.scalar_one_or_none()

            if not facility_status:
                facility_status = FacilityStatus(
                    code=status["code"],
                )

            facility_status.label = status["label"]

            try:
                session.add(facility_status)
                await session.commit()
                logger.debug(f"Loaded status {facility_status.code}")
            except Exception:
                logger.error(f"Have {facility_status.code}")
                await session.rollback()


async def load_networks() -> None:
    """
    Load the networks fixture
    """
    fixture = load_data("networks.json", from_fixture=True)

    async with SessionLocalAsync() as session:
        for network in fixture:
            network_model_query = await session.scalars(select(Network).where(Network.code == network["code"]))
            network_model = network_model_query.unique().one_or_none()

            if not network_model:
                network_model = Network(code=network["code"])

            network_model.label = network["label"]
            network_model.country = network["country"]
            network_model.timezone = network["timezone"]
            network_model.timezone_database = network["timezone_database"]
            network_model.offset = network["offset"]
            network_model.interval_size = network["interval_size"]
            network_model.network_price = network["network_price"]

            if "interval_shift" in network:
                network_model.interval_shift = network["interval_shift"]

            if "export_set" in network:
                network_model.export_set = network["export_set"]

            try:
                session.add(network_model)
                await session.commit()
                logger.debug(f"Loaded network {network_model.code}")
            except Exception:
                logger.error(f"Have {network_model.code}")
                await session.rollback()


async def load_network_regions() -> None:
    """
    Load the network region fixture
    """
    fixture = load_data("network_regions.json", from_fixture=True)

    async with SessionLocalAsync() as session:
        for network_region in fixture:
            result = await session.scalars(
                select(NetworkRegion).where(
                    and_(NetworkRegion.code == network_region["code"], NetworkRegion.network_id == network_region["network_id"])
                )
            )
            network_region_model = result.unique().one_or_none()

            if not network_region_model:
                network_region_model = NetworkRegion(code=network_region["code"])

            network_region_model.network_id = network_region["network_id"]

            try:
                session.add(network_region_model)
                await session.commit()
                logger.debug(f"Loaded network region {network_region_model.code}")
            except Exception:
                logger.error(f"Have {network_region_model.code}")
                await session.rollback()


"""
    BOM Fixtures
"""


def parse_date(date_str: str) -> date:
    dt = datetime.strptime(date_str, "%Y%m%d")
    return dt.date()


def parse_fixed_line(line: str) -> tuple[str, str, str, date, Decimal, Decimal]:
    """
    Parses a fixed-width CSV from the funky BOM format
    """
    return (
        str(line[:6]),
        str(line[8:11]).strip(),
        str(line[18:59]).strip(),
        parse_date(line[59:67]),
        Decimal(line[75:83]),
        Decimal(line[84:]),
    )


async def load_bom_stations_csv() -> None:
    """
    Imports the BOM fixed-width stations format

    Made redundant with the new JSON
    """

    station_csv = load_data("stations_db.txt", from_fixture=True)

    lines = station_csv.split("\n")

    async with SessionLocalAsync() as session:
        for line in lines:
            code, state, name, registered, lng, lat = parse_fixed_line(line)

            station = await session.scalars(select(BomStation).where(BomStation.code == code))
            station = station.one_or_none()

            if not station:
                station = BomStation(
                    code=code,
                    state=state,
                    name=name,
                    registered=registered,
                )

            station.geom = f"SRID=4326;POINT({lat} {lng})"

            try:
                session.add(station)
                await session.commit()
            except Exception:
                logger.error(f"Have {station.code}")
                await session.rollback()


async def load_bom_stations_json() -> None:
    """
    Imports BOM stations into the database from bom_stations.json

    The json is obtained using scripts/bom_stations.py
    """
    async with SessionLocalAsync() as session:
        bom_stations = load_data("bom_stations.json", from_project=True)
        bom_capitals = load_data("bom_capitals.json", from_project=True)

        codes = []

        if not bom_stations:
            logger.error("Could not load bom stations")

        stations_imported = 0

        for bom_station in bom_stations:
            if "code" not in bom_station:
                logger.error("Invalid bom station ..")
                continue

            if bom_station["code"] in codes:
                continue

            codes.append(bom_station["code"])

            station_query = await session.scalars(select(BomStation).where(BomStation.code == bom_station["code"]))
            station = station_query.one_or_none()

            if not station:
                logger.info("New BOM station: %s", bom_station["name"])

                station = BomStation(
                    code=bom_station["code"],
                )

            station.name = bom_station["name_full"]
            station.name_alias = bom_station["name"]
            station.website_url = bom_station["url"]
            station.feed_url = bom_station["json_feed"]
            station.priority = 5
            station.state = bom_station["state"]
            station.altitude = bom_station["altitude"]

            if "web_code" in bom_station:
                station.web_code = bom_station["web_code"]

            if bom_station["code"] in bom_capitals:
                station.is_capital = True
                station.priority = 1

            station.geom = "SRID=4326;POINT({} {})".format(bom_station["lng"], bom_station["lat"])

            stations_imported += 1
            session.add(station)

        logger.info(f"BoM: Imported {stations_imported} stations")
        await session.commit()


async def load_fixtures() -> None:
    await load_fueltechs()
    # await load_facilitystatus()
    # await load_networks()
    # await load_network_regions()
    # await load_bom_stations_json()
    # await rooftop_facilities()


if __name__ == "__main__":
    asyncio.run(load_fixtures())
