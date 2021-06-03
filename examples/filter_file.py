"""
    This example scans a CSV file and extracts only the rows with with specific
    first name values.
    If shows how to:
    - 
"""

from seesv import DelimitedFile
import csv

def log_progress(percent_complete: int):
    """
    This function accepts an integer representing the percent complete,
    and prints out a loading message with the percentage.
    """
    print(f'\rLoading - {percent_complete}%', end='')


def filterFile():

    source_file = 'test.csv'

    '''
    We're going to instantiate a DelimitedFile object with the following parameters:
    - name/path of the source CSV file
    - skip_lines = 1 tells DelimitedFile to ignore 1 line at the top of the file
    - progress_reporter is reference to our log_progress function. This will be at intervals
          as the file is being scanned and indexed by the open() method.
    - error_reporter is a reference to a function that will be called by open() if any errors
          are encountered while scanning the file. Here we're showing that a lambda can be
          used instead of a defined function.
    The has_header parameter is not supplied, so the default (True) will be used.
    '''
    inputFile = DelimitedFile(
        source_file,
        skip_lines=1,
        progress_reporter=log_progress,
        error_reporter=lambda msg: print("BIG TROUBLE! ", msg))

    print()

    '''
    Ok. Let's get to work!
    We're going to call open(), which will kick off the scanning/indexing of the file.
    We're also going to open a target CSV file into which we will write our filtered records.
    '''
    with inputFile.open() as incsv, open('output.csv', 'w', encoding='utf-8', errors='replace') as out:
        ocsv = csv.writer(out, csv.unix_dialect, quoting=csv.QUOTE_MINIMAL)
        ocsv.writerow(incsv.header)

        '''
        In addition to a headers property containing an array of column names, DelimitedFile provides
        a columns property that is a dictionary of column names mapped to their column positions.
        This will be helpful for accessing the FIRST_NAME column by name, so we can filter on its
        values.
        '''
        nameColumn = incsv.columns['FIRST_NAME']
        rowNum = 0
        exported = 0
        names = set([ 'Mickie', 'Wolfie', 'Jeremy', 'Phillida' ])

        print("\nExporting...")

        '''
        Calling get_rows() with just the starting row number and no row count tells
        DelimitedFile to stream all rows starting from the specified row (0 being the 1st row).
        '''
        for row in incsv.get_rows(0):
            rowNum += 1

            if row[nameColumn] in names:
                exported += 1
                ocsv.writerow(row)

            if rowNum % 10_000 == 0:
                print(f'\rRow: {rowNum:9,}  Exported: {exported:9,}', end='')

        out.flush()
        print(f'\rRow: {rowNum:9,}  Exported: {exported:9,}')
        print("Done")


if __name__ == '__main__':
    filterFile()
