from opennem.importer.aemo_gi import run_import_nem_gi
from opennem.importer.aemo_rel import run_import_nem_rel
from opennem.importer.mms import run_import_mms


def run_all():
    run_import_mms()
    run_import_nem_rel()
    run_import_nem_gi()
