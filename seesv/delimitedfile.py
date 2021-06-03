import csv
import mmap
from pathlib import Path
from array import array
from io import StringIO
from contextlib import AbstractContextManager
from typing import Union
import codecs


# .................................................................................................
class DelimitedFile(AbstractContextManager):

    def __init__(
        self,
        filePath: str,
        skip_rows: int = 0,
        has_header: bool = True,
        progress_reporter=None,
        error_reporter=None
    ) -> None:
        if not filePath:
            raise ValueError("A valid file path must be supplied.")

        self.filePath = Path(filePath)

        if not self.filePath.exists():
            raise ValueError("A valid file path must be supplied.")

        self.progress_reporter = progress_reporter
        self.error_reporter = error_reporter
        self.skip_rows = skip_rows
        self.has_header = has_header
        self.row_index = array('I', [])
        self.row_count = 0
        self.file_size = 0
        self.header = []
        self.columns = {}
        self.source_file = None

    # .............................................................................................
    def __enter__(self):
        ...
        """
            Scans the source file to catalog the line positions, line count, and file size.
        """
        return self.open() if not self.source_file else self

    # .............................................................................................
    def __exit__(self, *exc):
        self.close()
        return False

    # .............................................................................................
    def open(self):
        self.file_size = self.filePath.stat().st_size
        self.source_file = codecs.open(str(self.filePath), 'r', encoding='utf-8', errors='replace')

        # The source file is opened as a memory-mapped file. Scanning a memory-mapped file was found
        # to be much faster than scanning bytes from a the usual file opened with os.open().
        mm = mmap.mmap(self.source_file.fileno(), length=0, access=mmap.ACCESS_READ)

        # The row_index array is created using the array module's implementation of an array
        # instead of the normal Python arrays. Arrays created using the array module are typed
        # and in the case of row_index, it uses only 13% of the memory consumed by a normal
        # Python array.
        self.row_index = array('I', [0] * 100_000)
        self.row_count = 0
        current_pos = 0
        percent_done = 0
        capacity = len(self.row_index)

        for _ in range(self.skip_rows):
            _, _ = self._read_line(self.source_file)

        current_pos = self._read_header(self.source_file)

        mm.seek(current_pos)

        while True:
            self.row_index[self.row_count] = current_pos
            self.row_count += 1

            # We need to expand the row_index array if we have reached the capacity of the array.
            # Arrays are fixed size, so we need to do this expansion manually.
            # Each time we resize the array, we double the size. There will most likely be a decent
            # amount of empty slots after we finish building the index, so at the end, we will truncate
            # the final array to the number of items it actually holds.
            if self.row_count >= capacity:
                capacity = capacity * 2
                n = array('I', [0] * capacity)

                for i, v in enumerate(self.row_index):
                    n[i] = v

                self.row_index = n

            if (i := mm.find(b"\n", current_pos)) < 0:
                break

            current_pos = i + 1

            if self.row_count % 100_000 == 0:
                percent_done = int((current_pos / self.file_size) * 100)
                self._log_progress(percent_done)

        # if current_pos < self.file_size:
        #     self.row_count += 1

        mm.close()
        percent_done = int((current_pos / self.file_size) * 100)
        self._log_progress(percent_done)

        # Truncate the row_index array to the size of its actual contents.
        self.row_index = self.row_index[0:self.row_count]

        return self

    # .............................................................................................
    def close(self):
        if self.source_file:
            self.source_file.close()
            self.row_index = array('I', [])
            self.row_count = 0
            self.file_size = 0
            self.header = []
            self.columns = {}
            self.source_file = None

    # .............................................................................................
    def get_row(self, row_number: int) -> Union[list, None]:
        if row_number <= self.row_count:
            line_position = self.row_index[row_number]
            self.source_file.seek(line_position, 0)
            raw_line = StringIO(self.source_file.readline())
            cr = csv.reader(raw_line)
            return next(cr)

        return None

    # .............................................................................................
    def get_rows(self, start_row: int, row_count: int = -1):
        if start_row <= self.row_count:
            line_position = self.row_index[start_row]
            self.source_file.seek(line_position, 0)

            # The csv reader is created with a custom iterator so that invalid characters, which
            # seem to get into files fairly often, can be stripped out of each row before the csv module 
            # parses the row. This eliminates some classes of CSV errors.
            csv_reader = csv.reader((line.replace('\0', '') for line in self.source_file), delimiter=',')
            rowNum = 0

            for row in csv_reader:
                yield row
                rowNum += 1

                if row_count > 0 and rowNum >= row_count:
                    break

    # .............................................................................................
    def get_rows_as_list(self, start_row: int, row_count: int):
        return list(self.get_rows(start_row, row_count))

    # .............................................................................................
    def _log_progress(self, percent_done: int):
        if self.progress_reporter:
            self.progress_reporter(percent_done)

    # .............................................................................................
    def _logError(self, message: str):
        if self.error_reporter:
            self.error_reporter(message)

    # .............................................................................................
    def _read_header(self, source) -> int:
        if not self.has_header:
            return source.tell()

        headerLine, next_line_start = self._read_line(source)
        cr = csv.reader(StringIO(headerLine))
        self.header = next(cr)
        cr = None

        for i, c in enumerate(self.header):
            self.columns[c] = i

        return next_line_start

    # .............................................................................................
    def _read_line(self, file, start=-1):
        if start > 0 and start != file.tell():
            file.seek(start, 0)

        hwriter = StringIO()

        while (char := file.read(1)) != '\n':
            hwriter.write(char)

        return (hwriter.getvalue().strip(), file.tell())

