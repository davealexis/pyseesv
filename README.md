# SeeSV-Lib



SeeSV-Lib is a library for providing fast access to data in very large delimited data files (CSV, TSV, pipe-delimited, etc) as memory-efficient as possible.

This library grew out of the frustration of reading and analyzing very large (multi-gigabyte, 5+ million row) CSV files (and other delimited file formats). There are few options for reading these files to quickly find problems, generate a filtered subset, or find specific data. There was the constant need for both a command line tool that can be used on a server via an SSH terminal connection and a desktop tool that can quickly churn through huge files. There are many tools out there, but most fall flat when handling very large files - either they take forever to open the file or (and) end up crashing by running out of memory.

The goal with SeeSV is to provide both a re-usable library that encapsulates handling delimited files and a cross-platform desktop GUI that builds on top of the library to provide the user with the best possible experience and feature set.

This project provides the re-usable Python library that can be used to build tools or programmatically inspect files.



## Design



### SeeSV-Lib Features

- Blazing fast loading of files so that the user gets to a productive state with the data within seconds.
- Minimal memory consumption even for extremely large files.
- The ability to jump to any area of a file in constant time, then provide a bounded or unbounded stream of parsed records from that point.
- Handle files with or without headers, and files with extra header lines (like file summary metadata, etc).
- Simple, intuitive API



### Design

When a file is opened, SeeSV performs a number of discovery tasks:

1. Extract the column headers, if the file contains any. The headers are stored in a list accessible as a property of the DelimitedFile object.
2. Scans the file to generate an internal index of the byte positions of the start of every line (row) in the file, excluding the headers. This index is the only  aspect of SeeSV that may use a significant amount of memory. In testing, the scan of a 5 million row file (2.3GB) took around 4 seconds and produced an index using 18MB of memory. The index enables a constant-time seek to any part of a file by row number.
3. As a consequence of step 2, the row count is obtained and made available as a property of the DelimitedFile object.
4. File size is also made available through a property.

The DelimitedFile class encapsulates all of the functionality. It is implemented as a context manager, allowing with the `with` block to ensure that the source file is closed and memory released when done with the file. Use of the context manager interface is optional, and a developer can choose the manual route of calling `.open()` and `.close()`.



## Examples



**Example 1:** a file with the context manager interface, assuming that the file has a header line:

```python
from seesvlib import DelimitedFile
...

with DelimitedFile('/path/to/test.csv') as csvFile:
    ...
    # Array of column headers is available as csvFile.header
    
    # Get 1,000 rows starting from row 25,000
    for row in csvFile.getRows(25000, 1000):
        # work with row
```



**Example 2:** Similar to Example 1, except the file contains two extra metadata lines at the top before the column headers that we want to skip:

```python
with DelimitedFile('/path/to/test.csv', skipRows=2) as csvFile:
    ...
    # Get 1,000 rows starting from row 25,000
    for row in csvFile.getRows(25000, 1000):
        # work with row
```



**Example 3:** The file does not contain a header row, so we just want access to the data:

```python
with DelimitedFile('/path/to/test.csv', hasHeader=False) as csvFile:
    ...
    # csvFile.header is not populated
    
    # Get 1,000 rows starting from row 25,000
    for row in csvFile.getRows(25000, 1000):
        # work with row
```



**Example 4:** We don't want to use the context manager interface:

```python
csvFile = DelimitedFile('/path/to/test.csv')
csvFile.open()
...
csvFile.close()
```



**Example 5:** We just want to get a single row from the file:

```python
with DelimitedFile('/path/to/test.csv') as csvFile:
    row = csvFile.getRow(1500)
    
    # Get the last row of the file
    row = csvFile.getRow(csvFile.rowCount)
```



**Example 6:**  Get all rows from a given point till the end of the file:

```python
with DelimitedFile('/path/to/test.csv') as csvFile:
    for row in csvFile.getRows(1500):
        ...
    # Get last 100 rows in the file
    for row in csvFile.getRows(csvFile.rowCount - 99):
        ...
```



## Roadmap

The following are some of the features that are coming:

- Automatically detect column data types
- Allow user to supply column schema.
- Support for file formats other than CSV:
  - Tab-separated
  - Pipe-delimited
  - JSON (?)
  - Compressed files (e.g. myfile.csv.gz)
- Auto-detect which line contains headers (e.g. ignore any metadata rows at the top of the file)
- Filters
- SQL Queries
- Projections - get specified columns instead of all columns