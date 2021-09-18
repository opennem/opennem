import pytest

from opennem.core.normalizers import station_name_cleaner


@pytest.mark.parametrize(
    ["station_name", "station_name_clean"],
    [
        # Simple strips
        ("Test Power Station", "Test"),
        ("Test Wind Farm", "Test"),
        ("Test Solar Farm", "Test"),
        ("Test Solar Project", "Test"),
        ("Test (Solar Project)", "Test"),
        ("Test SF", "Test"),
        #
        ("Hepburn Wind", "Hepburn"),
        ("Lake Bonney Battery", "Lake Bonney"),
        ("White Rock Wind and Battery", "White Rock"),
        ("White Rock Wind and", "White Rock"),
        ("Jounama (Mini Hydro)", "Jounama"),
        ("Hallett Power Station", "Hallett Power Station"),
        ("Grosvenor 1 Waste Coal Mine Gas Power Station", "Grosvenor 1"),
        ("Yallourn 'W' Power Station", "Yallourn W"),
        ("Wyndham Waste Disposal Facility", "Wyndham"),
        ("Eastern Creek LFG PS Units 1-4", "Eastern Creek"),
        ("Tamar Valley Combined Cycle", "Tamar Valley"),
        ("Broadmeadows Landfill", "Broadmeadows"),
        ("Bulgana Green Power Hub - Units", "Bulgana Green Power Hub"),
        ("Cleantech Biogas", "Cleantech"),
        ("Earthpower Biomass", "Earthpower"),
        ("earthpower biomass", "Earthpower"),
        ("Collector Wind Farm 1", "Collector"),
        ("Collie G1", "Collie"),
        ("Lake Bonney Bess1", "Lake Bonney"),
        ("Muja Cd", "Muja CD"),
        # Combined names
        ("Catagunya / Liapootah / Wayatinah", "Catagunya / Liapootah / Wayatinah"),
        ("Catagunya / Liapootah /Wayatinah", "Catagunya / Liapootah / Wayatinah"),
        ("catagunya/liapootah /wayatinah", "Catagunya / Liapootah / Wayatinah"),
        ("catagunya/liapootah /woy woy power station", "Catagunya / Liapootah / Woy Woy"),
        # mappings
        ("SA Government Virtual Power Plant - stage 1", "SA VPP"),
        ("Hornsdale Power Reserve Unit 1", "Hornsdale Power Reserve"),
        ("University of Melbourne Archives Brunswick", "UoM Archives Brunswick"),
        ("Energy Brix Complex", "Morwell"),
        ("Swanbank B Power Station & Swanbank E Gas Turbine", "Swanbank B"),
        ("Swanbank B", "Swanbank B"),
        ("Swanbank E", "Swanbank E"),
        ("Tailem Bend 1", "Tailem Bend"),
        ("Hallett 1 Wind Farm", "Hallett 1 Wind Farm"),
        ("Hallett 2 Wind Farm", "Hallett 2 Wind Farm"),
    ],
)
def test_station_name_cleaner(station_name: str, station_name_clean: str) -> None:
    subject = station_name_cleaner(station_name)

    assert subject == station_name_clean, "Clean name matches"


def test_station_name_cleaner_hallet_is_three_units() -> None:
    hallet_names = [
        "Hallett Power Station",
        "Hallett 1 Wind Farm",
        "Hallett 2 Wind Farm",
    ]
    hallet_names_cleaned = list(set([station_name_cleaner(i) for i in hallet_names]))

    print(hallet_names_cleaned)

    assert len(hallet_names) == len(
        hallet_names_cleaned
    ), "Hallet should have three distinct names"
