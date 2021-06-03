from pathlib import Path
from seesvlib import __version__, DelimitedFile


# .................................................................................................
def test_version():
    assert __version__ == '0.1.0'


# .................................................................................................
def test_load_file():
    with DelimitedFile(get_file_path('test.csv')) as csv_file:
        assert csv_file.has_header
        assert csv_file.header[0] == 'ID'
        assert csv_file.row_count == 1_000


# .................................................................................................
def test_open():
    csv_file = DelimitedFile(get_file_path('test.csv'))
    assert not csv_file.header
    assert not csv_file.columns
    assert csv_file.row_count == 0

    csv_file.open()
    assert csv_file.header
    assert csv_file.row_count != 0
    assert len(csv_file.columns) == 8

    csv_file2 = DelimitedFile(get_file_path('test.csv'))

    with csv_file2.open():
        assert csv_file2.row_count != 0

    assert csv_file2.row_count == 0


# .................................................................................................
def test_larger_file():
    with DelimitedFile(get_file_path('test_10000.csv')) as csv_file:
        assert csv_file.has_header
        assert csv_file.header[0] == 'ID' and csv_file.header[1] == 'FIRST_NAME'
        assert csv_file.row_count == 10_000


# .................................................................................................
def test_fail_if_1st_header_not_skipped():
    with DelimitedFile(get_file_path('test_extra_header.csv')) as csv_file:
        assert csv_file.header[0] != 'ID' and csv_file.header[0] == 'SKIP THIS LINE'


# .................................................................................................
def test_skip_1st_header():
    with DelimitedFile(get_file_path('test_extra_header.csv'), skip_lines=1) as csv_file:
        assert csv_file.header[0] == 'ID' and csv_file.header[1] == 'FIRST_NAME'
        assert csv_file.row_count == 100


# .................................................................................................
def test_no_header():
    with DelimitedFile(get_file_path('test_no_header.csv'), skip_lines=0, has_header=False) as csv_file:
        assert not csv_file.header
        assert csv_file.row_count == 100


# .................................................................................................
def test_get_1_row():
    with DelimitedFile(get_file_path('test.csv')) as csv_file:
        line = csv_file.get_row(0)

        print(csv_file.row_index[0])
        print(line)
        assert line[0] == '1'
        assert line[1] == 'Vern'

        # Get last row of the file
        assert csv_file.get_row(csv_file.row_count - 1)[1] == 'LastRow'

    with DelimitedFile(get_file_path('test_extra_header.csv'), skip_lines=1) as csv_file:
        line = csv_file.get_row(0)

        assert line[0] == '1'
        assert line[1] == 'Vern'


# .................................................................................................
def test_get_10_rows():
    with DelimitedFile(get_file_path('test.csv')) as csv_file:
        rows = list(csv_file.get_rows(499, 200))
        assert len(rows) == 200
        assert rows[0][0] == '500'

        rows = csv_file.get_rows_as_list(499, 200)
        assert len(rows) == 200
        assert rows[0][0] == '500'


# .................................................................................................
def test_get_rows_to_end():
    with DelimitedFile(get_file_path('test.csv')) as csv_file:
        rows = list(csv_file.get_rows(csv_file.row_count - 10))
        assert len(rows) == 10

        rows = list(csv_file.get_rows(csv_file.row_count - 200))
        assert len(rows) == 200

# .................................................................................................
def get_file_path(test_file: str) -> str:
    cwd = Path(__file__).parent
    return str(cwd / 'data' / test_file)
