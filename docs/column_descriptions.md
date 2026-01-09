---
orphan: true
---

# Index Tables Column Descriptions

```{note}
This page has been superseded by the comprehensive [Index Tables Reference](indices_reference.md) page, which provides automatically-generated, up-to-date documentation for all index tables including:

- Complete column descriptions from the official schemas
- Table relationship diagrams
- Schema version information
- All available index tables (not just the main ones)

**Please visit [Index Tables Reference](indices_reference.md) for the complete documentation.**
```

## Quick Links

For detailed information about each index table, see:

- [Index Tables Reference](indices_reference.md) - **Complete reference with all
  tables and columns**
- `index` table - Main metadata table (series-level)
- `sm_index` table - Slide microscopy metadata (series-level)
- `sm_instance_index` table - Slide microscopy metadata (instance-level)
- `clinical_index` table - Clinical data dictionary
- `collections_index` table - Collection metadata
- `analysis_results_index` table - Analysis results metadata
- `prior_versions_index` table - Historical version tracking

All tables are documented in detail on the
[Index Tables Reference](indices_reference.md) page.

## Overview

`idc-index` wraps indices of IDC data: tables containing the most important
metadata attributes describing the files available in IDC. The main metadata
index is available in the `index` variable (which is a pandas `DataFrame`) of
`IDCClient`. Additional index tables such as the `clinical_index` contain
non-DICOM clinical data or slide microscopy specific tables (indicated by the
prefix `sm`) include metadata attributes specific to slide microscopy images.

For complete, up-to-date column descriptions and schemas, please refer to the
[Index Tables Reference](indices_reference.md) page.
