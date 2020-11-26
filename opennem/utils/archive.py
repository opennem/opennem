"""
    Module to handle zip files


"""
import io
from io import BytesIO
from typing import IO
from zipfile import ZipFile

# limit how many zips within zips we'll parse
# 0 means all
ZIP_LIMIT = 0


def chain_streams(streams, buffer_size=io.DEFAULT_BUFFER_SIZE):
    """
    Chain an iterable of streams together into a single buffered stream.
    Usage:
        def generate_open_file_streams():
            for file in filenames:
                yield open(file, 'rb')
        f = chain_streams(generate_open_file_streams())
        f.read()
    """

    class ChainStream(io.RawIOBase):
        def __init__(self):
            self.leftover = b""
            self.stream_iter = iter(streams)
            try:
                self.stream = next(self.stream_iter)
            except StopIteration:
                self.stream = None

        def readable(self):
            return True

        def _read_next_chunk(self, max_length):
            if self.leftover:
                return self.leftover
            elif self.stream is not None:
                return self.stream.read(max_length)
            else:
                return b""

        def readinto(self, b):
            buffer_length = len(b)
            chunk = self._read_next_chunk(buffer_length)
            while len(chunk) == 0:
                # move to next stream
                if self.stream is not None:
                    self.stream.close()
                try:
                    self.stream = next(self.stream_iter)
                    chunk = self._read_next_chunk(buffer_length)
                except StopIteration:
                    # No more streams to chain together
                    self.stream = None
                    return 0  # indicate EOF
            output, self.leftover = (
                chunk[:buffer_length],
                chunk[buffer_length:],
            )
            b[: len(output)] = output
            return len(output)

    return io.BufferedReader(ChainStream(), buffer_size=buffer_size)


def fix_central_directory(zfile: BytesIO) -> BytesIO:
    """
    Fixes the central directory on bad zip files
    """
    # @NOTE See http://bugs.python.org/issue10694
    content = zfile.read()

    # reverse find: this string of bytes is the end of
    #  the zip's central directory.
    pos = content.rfind(b"\x50\x4b\x05\x06")

    if pos > 0:
        zfile.seek(pos + 20)
        zfile.truncate()
        zfile.write(b"\x00\x00")  # Zip file comment length: 0 byte length;
        zfile.seek(0)

    return zfile


def stream_zip_contents(file_obj: IO[bytes], mode: str = "w"):
    """
    Steram out the entire contents of a zipfile
    handling embedded zips

    mode param is to compat with external libs like smart_open
    """
    with ZipFile(file_obj) as zf:
        # If there is only one file in the archive return it
        if len(zf.namelist()) == 1:
            return zf.open(zf.namelist()[0])

        c = []
        stream_count = 0

        for filename in zf.namelist():
            if filename.endswith(".zip"):
                if ZIP_LIMIT > 0 and stream_count >= ZIP_LIMIT:
                    continue

                c.append(stream_zip_contents(zf.open(filename), mode))
                stream_count += 1
            else:
                c.append(zf.open(filename))

        return chain_streams(c)
