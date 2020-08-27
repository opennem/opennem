# pylint: skip-file
# python3
from io import BytesIO, StringIO
from zipfile import BadZipfile, ZipFile

import pandas as pd


class ZipFileStreamer(ZipFile):
    """ZipFile subclass, with method to extract ZipFile as byte or string stream to memory"""

    def __init__(
        self,
        filename="/data/marble/nemweb/ARCHIVE/DispatchIS_Reports/PUBLIC_DISPATCHIS_20170208.zip",
    ):
        """Open the ZIP file with mode read "r", write "w" or append "a" """
        ZipFile.__init__(self, filename)
        self.member_count = len(self.filelist)

    def extract_stream(self, member, IO=BytesIO):
        """	Extract a member from the archive as a byte stream or string
        steam, using its full name. `member' may be a filename or a
        ZipInfo object. """
        return IO(self.read(member))


def zip_streams(
    fileobject="/data/marble/nemweb/ARCHIVE/DispatchIS_Reports/PUBLIC_DISPATCHIS_20140208.zip",
):
    """Generator that yields each memeber of a zipfile as a BytesIO stream.
    Can take a filename or file-like object as an argument (including BytesIO or StringIO"""
    with ZipFileStreamer(fileobject) as zf:
        for filename in zf.namelist():
            yield filename, zf.extract_stream(filename)


class NemFile:
    def __init__(self, fileobject):
        self.__table_reader(fileobject)

    def __table_reader(self, fileobject):
        self.__dict__ = {}

        for line in fileobject.readlines():
            rows = line.decode().split(",")
            table = "{0}_{1}".format(rows[1], rows[2])

            # new table
            if rows[0] == "I":
                if table == "DISPATCH_OFFERTRK":
                    break
                self.__dict__[table] = line

            # append data to each table
            elif rows[0] == "D":
                self.__dict__[table] += line

        self.__dict__ = {
            table: pd.read_csv(BytesIO(self.__dict__[table]))
            for table in self.__dict__
        }

    def __iter__(self):
        for table in self.__dict__:
            yield table


def load_nemfile(f="PUBLIC_DISPATCHIS_201309150010_0000000246668929.zip"):
    with ZipFileStreamer(f) as zf:
        if zf.member_count == 1:
            filename = zf.namelist()[0]
            zfs = zf.extract_stream(filename)
            return NemFile(zfs)
        else:
            raise Exception("More than one file in zipfile")
