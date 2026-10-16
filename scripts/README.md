# Utility Scripts

This directory contains utility scripts for maintaining and generating
documentation for the `idc-index` package.

## generate_indices_docs.py

Automatically generates comprehensive documentation for all available index
tables in IDC.

### Purpose

This script:

1. Instantiates `IDCClient` from `idc_index`
2. Uses the built-in index table discovery functionality to find all available
   indices
3. Fetches schemas for all tables from `idc-index-data`
4. Generates a markdown documentation page with column descriptions for each
   table
5. Creates a Mermaid diagram showing relationships between tables based on
   shared column names

### Usage

```bash
# Run from the repository root
python scripts/generate_indices_docs.py
```

The script will generate `docs/indices_reference.md` containing:

- An overview of all available index tables
- A Mermaid ER diagram showing table relationships
- Detailed column descriptions for each table

### Output

The generated documentation includes:

- Table names and descriptions
- Column names, types, modes (NULLABLE, REQUIRED, REPEATED)
- Column descriptions from the schema
- Visual diagram of table relationships based on shared key columns

### Regenerating Documentation

Run this script whenever:

- A new version of `idc-index-data` is released
- New index tables are added
- Schema definitions are updated
