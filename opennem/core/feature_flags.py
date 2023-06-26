"""" OpenNEM Feature Flags  """
from opennem import settings

FEATURE_FLAG_LIST = [
    "workers_run",
    "run_crawlers",
    "flows_and_emissions_v3",
    "redirect_api_static",
    "per_interval_aggregate_processing",
    "show_emissions_in_power_outputs",
]


def get_list_of_enabled_features() -> list[str]:
    """Gets a list of the enabled features for this environment"""

    enabled_feature_flags = []
    for feature_flag in FEATURE_FLAG_LIST:
        if hasattr(settings, feature_flag):
            if getattr(settings, feature_flag) is True:
                enabled_feature_flags.append(feature_flag)

    return enabled_feature_flags


if __name__ == "__main__":
    print(get_list_of_enabled_features())
