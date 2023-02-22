from datetime import datetime

from freezegun import freeze_time

from opennem.pipelines.crontab import network_interval_crontab
from opennem.schema.network import NetworkAEMORooftop, NetworkNEM, NetworkWEM


# NEM
@freeze_time("2022-02-17T00:00:10+10:00")
def test_network_interval_crontab_nem_hits() -> None:
    """Unit test cronttab hits"""
    crontab_return = network_interval_crontab(network=NetworkNEM, number_minutes=2)
    assert crontab_return(datetime.now()) is True


@freeze_time("2022-02-17T00:09:10+10:00")
def test_network_interval_crontab_nem_misses() -> None:
    """Unit test cronttab hits"""
    crontab_return = network_interval_crontab(network=NetworkNEM, number_minutes=2)
    assert crontab_return(datetime.now()) is False


# WEM
@freeze_time("2022-02-17T00:00:10+10:00")
def test_network_interval_crontab_wem_hits() -> None:
    """Unit test cronttab hits"""
    crontab_return = network_interval_crontab(network=NetworkWEM, number_minutes=2)
    assert crontab_return(datetime.now()) is True


@freeze_time("2022-02-17T00:09:10+10:00")
def test_network_interval_crontab_wem_misses() -> None:
    """Unit test cronttab hits"""
    crontab_return = network_interval_crontab(network=NetworkWEM, number_minutes=2)
    assert crontab_return(datetime.now()) is False


# Rooftop
@freeze_time("2022-02-17T00:00:10+10:00")
def test_network_interval_crontab_rooftop_hits() -> None:
    """Unit test cronttab hits"""
    crontab_return = network_interval_crontab(network=NetworkAEMORooftop, number_minutes=2)
    assert crontab_return(datetime.now()) is True


@freeze_time("2022-02-17T00:09:10+10:00")
def test_network_interval_crontab_rooftop_misses() -> None:
    """Unit test cronttab hits"""
    crontab_return = network_interval_crontab(network=NetworkAEMORooftop, number_minutes=2)
    assert crontab_return(datetime.now()) is False
