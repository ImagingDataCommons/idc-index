# IDC Index Architecture Guide

This document provides a developer-focused overview of the `idc-index` codebase
architecture.

## Project Structure

```text
idc-index/
├── idc_index/
│   ├── __init__.py          # Package exports (IDCClient, exceptions)
│   ├── index.py             # Main IDCClient class implementation
│   └── cli.py               # Command-line interface
├── tests/
│   ├── idcindex.py          # Main test suite for IDCClient
│   └── test_package.py      # Package-level tests
└── docs/
    └── ...
```

## Core Class: IDCClient

The main class is `IDCClient` in `idc_index/index.py`. It provides access to
DICOM metadata indices and download functionality.

### Initialization (`__init__`)

The constructor (lines ~88-158) performs:

1. **Load bundled indices** from `idc-index-data` package:
   - `self.index` - Main DICOM metadata index (always loaded)
   - `self.prior_versions_index` - Historical version data (always loaded)

2. **Initialize lazy-loaded indices** as `None`:
   - `self.sm_index` - Slide microscopy series metadata
   - `self.sm_instance_index` - Slide microscopy instance metadata
   - `self.clinical_index` - Clinical data index

3. **Discover available indices** via `_discover_available_indices()`:
   - Populates `self.indices_overview` dictionary
   - Uses `INDEX_METADATA` from `idc-index-data` package

4. **Setup utilities**:
   - `self.s5cmdPath` - Path to s5cmd executable for downloads
   - `self._duckdb_conn` - Reusable DuckDB connection for SQL queries

### Index Management

#### `indices_overview` Dictionary

Central registry of all available indices. Structure:

```text
{
    "index": {
        "description": "Main IDC index...",
        "installed": True,           # Always True for bundled
        "url": None,                 # None for bundled indices
        "file_path": "/path/to/index.parquet",
        "schema": {...}              # JSON schema with column definitions
    },
    "sm_index": {
        "description": "Slide microscopy...",
        "installed": True/False,     # True if downloaded
        "url": "https://github.com/.../sm_index.parquet",
        "file_path": "/path/or/None",
        "schema": {...}
    },
    ...
}
```

#### Key Methods

| Method                          | Location | Purpose                                            |
| ------------------------------- | -------- | -------------------------------------------------- |
| `_discover_available_indices()` | ~156-221 | Populates `indices_overview` from `INDEX_METADATA` |
| `refresh_indices_overview()`    | ~223-233 | Refreshes the indices list                         |
| `fetch_index(index_name)`       | ~437-520 | Downloads/loads an index and sets class attribute  |
| `get_index_schema(index_name)`  | ~235-254 | Returns JSON schema for an index                   |

#### Index Loading Flow

```text
User calls fetch_index("sm_index")
    │
    ├─► Index already installed & loaded? → Return
    │
    ├─► Index installed but not loaded?
    │       └─► Load from disk: pd.read_parquet(filepath)
    │       └─► setattr(self, "sm_index", dataframe)
    │
    └─► Index not installed?
            └─► Download from URL
            └─► Save to disk
            └─► Load into memory
            └─► Update indices_overview["sm_index"]["installed"] = True
```

### SQL Query System

#### `sql_query()` Method (~2307-2329)

Executes SQL queries against loaded indices using DuckDB.

**How it works:**

1. Iterates over `indices_overview`
2. For each index, checks if DataFrame is loaded (`getattr(self, name, None)`)
3. Registers loaded DataFrames with DuckDB connection
4. Executes query and returns pandas DataFrame

**DuckDB Integration:**

- Uses `duckdb.connect()` for in-process database
- `conn.register(name, df)` creates virtual table from DataFrame (zero-copy)
- Re-registration is safe and updates the reference

### Data Download Methods

The class provides multiple download methods, all following similar patterns:

| Method                      | Purpose                                 |
| --------------------------- | --------------------------------------- |
| `download_dicom_series()`   | Download series by SeriesInstanceUID    |
| `download_dicom_studies()`  | Download studies by StudyInstanceUID    |
| `download_dicom_patients()` | Download all data for patient(s)        |
| `download_collection()`     | Download entire collection              |
| `download_from_manifest()`  | Download from s5cmd manifest file       |
| `download_from_selection()` | Download from IDC Portal selection file |

**Common patterns:**

- Use `s5cmd` for parallel downloads from AWS/GCP
- Support directory templates for organizing downloads
- Query indices using internal DuckDB SQL

### Internal Query Pattern

Many methods use DuckDB queries with local DataFrames:

```python
def some_method(self):
    # Create local variable from class attribute
    index = self.index

    # DuckDB finds 'index' in local scope automatically
    sql = """
        SELECT column1, column2
        FROM index
        WHERE condition = 'value'
    """
    result = duckdb.query(sql).df()
```

This "replacement scan" pattern works because DuckDB inspects the Python call
stack to find DataFrames by variable name.

## Testing

### Test Structure

Tests are in `tests/idcindex.py` using `unittest.TestCase`.

**Test class setup:**

```python
class TestIDCClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = IDCClient()  # Shared client instance
```

**Key test patterns:**

- Use `self.subTest()` for parameterized tests with clear failure attribution
- Use `tempfile.TemporaryDirectory()` for download tests
- Mock or skip network-dependent tests appropriately

### Running Tests

```bash
# All tests
uv run pytest tests/ -v

# Specific test
uv run pytest tests/idcindex.py::TestIDCClient::test_sql_queries -v

# Tests matching pattern
uv run pytest tests/idcindex.py -k "sql_query" -v
```

## Dependencies

### External Packages

| Package          | Purpose                                        |
| ---------------- | ---------------------------------------------- |
| `idc-index-data` | Provides INDEX_METADATA, bundled parquet files |
| `pandas`         | DataFrame operations                           |
| `duckdb`         | SQL query engine                               |
| `requests`       | HTTP downloads for non-bundled indices         |
| `s5cmd`          | Parallel cloud storage downloads               |
| `platformdirs`   | Cross-platform data directories                |

### Data Locations

```python
# Versioned index data (downloaded indices)
self.indices_data_dir = platformdirs.user_data_dir(
    "idc_index_data", "IDC", version=version("idc-index-data")
)

# IDC data (clinical files, etc.)
self.idc_data_dir = platformdirs.user_data_dir("IDC", "IDC", version=self.idc_version)
```

## Common Development Tasks

### Adding a New Index

1. Add index metadata to `idc-index-data` package's `INDEX_METADATA`
2. The index will automatically appear in `indices_overview`
3. Users can fetch it with `fetch_index("new_index_name")`
4. It will automatically be available in `sql_query()` after fetching

### Modifying SQL Query Behavior

The `sql_query()` method is at ~line 2307. Key considerations:

- All indices in `indices_overview` are automatically registered if loaded
- Uses `self._duckdb_conn` (created in `__init__`) for connection reuse
- `conn.register()` is zero-copy for pandas DataFrames

### Adding New Download Methods

Follow existing patterns:

1. Build SQL query to select relevant rows from `self.index`
2. Generate s5cmd manifest file
3. Execute download using `subprocess.run([self.s5cmdPath, ...])`
