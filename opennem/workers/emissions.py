# """
# OpenNEM Emissions Workers
# """


# def run_energy_update_days(
#     networks: Optional[List[NetworkSchema]] = None,
#     days: int = 1,
#     fueltech: str = None,
#     region: str = None,
# ) -> None:
#     """Run energy sum update for yesterday. This task is scheduled
#     in scheduler/db"""

#     if not networks:
#         networks = [NetworkNEM, NetworkWEM, NetworkAPVI, NetworkAEMORooftop]

#     for network in networks:

#         # This is Sydney time as the data is published in local time
#         tz = pytz.timezone(network.timezone)

#         # today_midnight in NEM time
#         today_midnight = datetime.now(tz).replace(
#             tzinfo=network.get_fixed_offset(), microsecond=0, hour=0, minute=0, second=0
#         )

#         date_max = today_midnight
#         date_min = today_midnight - timedelta(days=days)

#         regions = [i.code for i in get_network_regions(network)]

#         if region:
#             regions = [region.upper()]

#         if network == NetworkAPVI:
#             regions = ["WEM"]

#         for ri in regions:
#             run_energy_calc(
#                 date_min,
#                 date_max,
#                 network=network,
#                 fueltech_id=fueltech,
#                 run_clear=False,
#                 region=ri,
#             )


# def run_emission_flow_update_all(
#     network: NetworkSchema = NetworkNEM, fueltech: Optional[str] = None, run_clear: bool = False
# ) -> None:
#     """Runs energy update for all regions and all years for one-off
#     inserts"""
#     for year in range(DATE_CURRENT_YEAR, 1997, -1):
#         run_energy_update_archive(
#             year=year, fueltech=fueltech, network=network, run_clear=run_clear
#         )


# def run_emission_flow_update_region(region_code: str, network: NetworkSchema = NetworkNEM) -> None:
#     facility_seen_range = None

#     # catch me if you can
#     facility_seen_range = get_facility_seen_range(facility_codes)

#     run_energy_calc(
#         facility_seen_range.date_min,
#         facility_seen_range.date_max,
#         facility_codes=facility_codes,
#         network=network,
#     )


# # debug entry point
# if __name__ == "__main__":
#     run_energy_update_all()
