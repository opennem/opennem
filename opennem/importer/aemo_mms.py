from pathlib import Path

MMS_DATA_DIR = "~/Projects/Opennem/data/mms/"
MMS_DATA_PREFIX = "MMSDM_"
MMS_APPEND_DATA_DIR_PATH = "MMSDM_Historical_Data_SQLLoader/DATA"
MMS_HISTORIC_DATA_DIR_PATH = "MMSDM_Historical_Data_SQLLoader/DATA"


def get_mms_sets(data_dir: str = MMS_DATA_DIR) -> list[Path]:
    """
    Finds MMS data sets in a directory and returns
    all paths sorted in chronological order

    """

    data_path = Path(data_dir).expanduser().resolve()

    if not data_path.is_dir():
        raise Exception(f"Not a directory: {data_dir}")

    mms_files = [
        d
        for d in data_path.iterdir()
        if d.is_dir() and d.name.startswith(MMS_DATA_PREFIX) and (d / MMS_HISTORIC_DATA_DIR_PATH).is_dir()
    ]

    mms_files = sorted(mms_files)

    return mms_files


def import_aemo_mms():
    mms_sets = get_mms_sets()

    for x in mms_sets:
        print(x)


if __name__ == "__main__":
    import_aemo_mms()
