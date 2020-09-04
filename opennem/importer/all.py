from opennem.importer.aemo_gi import gi_export
from opennem.importer.aemo_rel import rel_export
from opennem.importer.mms import mms_export
from opennem.importer.registry import registry_export


def run_all():
    mms_export()
    rel_export()
    gi_export()
    registry_export()
