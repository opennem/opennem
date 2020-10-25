"""
    support zip files and embedded nested zip files using just an overriden open
    command that supports http endpoints

"""

import io
import logging
import zipfile

from smart_open import open, register_compressor

smart_open_logger = logging.getLogger("smart_open")
smart_open_logger.setLevel(logging.INFO)

urllib_logger = logging.getLogger("urllib3")
urllib_logger.setLevel(logging.INFO)


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
            # Return 0 or more bytes from the current stream, first returning all
            # leftover bytes. If the stream is closed returns b''
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


ZIP_LIMIT = 0


def _handle_zip(file_obj, mode):
    with zipfile.ZipFile(file_obj) as zf:
        if len(zf.namelist()) == 1:
            return zf.open(zf.namelist()[0])

        c = []
        stream_count = 0

        for filename in zf.namelist():
            if filename.endswith(".zip"):
                if ZIP_LIMIT > 0 and stream_count >= ZIP_LIMIT:
                    continue

                c.append(_handle_zip(zf.open(filename), mode))
                stream_count += 1
            else:
                c.append(zf.open(filename))

        return chain_streams(c)


register_compressor(".zip", _handle_zip)
