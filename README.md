# idc-index

**Programmatic access to NCI Imaging Data Commons - the largest public
collection of cancer imaging data**

[![PyPI version][pypi-version]][pypi-link]
[![PyPI platforms][pypi-platforms]][pypi-link]
[![Actions Status][actions-badge]][actions-link]
[![Documentation Status][rtd-badge]][rtd-link]
[![Discourse Forum][discourse-forum-badge]][discourse-forum-link]

<!-- SPHINX-START -->

## What is Imaging Data Commons?

[NCI Imaging Data Commons (IDC)](https://imaging.datacommons.cancer.gov) is a
cloud-based platform providing researchers with free access to a large and
growing collection of cancer imaging data. This includes radiology images (CT,
MRI, PET), digital pathology slides, and more - all in standard DICOM format
with rich clinical and research metadata.

`idc-index` is the official Python package for querying IDC metadata and
downloading imaging data - no cloud credentials or complex setup required.

## Features

- **Query metadata with SQL** - Search across ~100TB of data using
  DuckDB-powered SQL queries
- **High-speed downloads** - Parallel downloads from AWS and Google Cloud public
  buckets via s5cmd
- **Browse hierarchically** - Navigate collections → patients → studies → series
  programmatically
- **Generate viewer URLs** - Create links to view images in OHIF (radiology) or
  Slim (pathology) web viewers
- **Command line interface** - Download data directly from the terminal with
  `idc` commands
- **No authentication required** - All data is publicly accessible

## Installation

```bash
pip install idc-index
```

Requires Python 3.10+. Downloads are powered by the bundled
[s5cmd](https://github.com/peak/s5cmd) tool.

### Keeping Up to Date

The package version is updated with each new IDC data release. Upgrade regularly
to access the latest collections and data:

```bash
pip install --upgrade idc-index
```

## Quick Start

### Explore and Download a Collection

```python
from idc_index import IDCClient

client = IDCClient.client()

# List all available collections
collections = client.get_collections()
print(f"IDC has {len(collections)} collections")

# Download a small collection (10.5 GB)
client.download_from_selection(collection_id="rider_pilot", downloadDir="./data")
```

### Query with SQL

Find CT scans of the chest and download them:

```python
from idc_index import IDCClient

client = IDCClient.client()

query = """
SELECT
    collection_id,
    PatientID,
    SeriesInstanceUID,
    SeriesDescription,
    series_size_MB
FROM index
WHERE Modality = 'CT'
  AND BodyPartExamined = 'CHEST'
LIMIT 10
"""

results = client.sql_query(query)
print(results)

# Download the matching series
client.download_dicom_series(
    seriesInstanceUID=results["SeriesInstanceUID"].tolist(), downloadDir="./chest_ct"
)
```

### Browse Data Hierarchy and View Images

Navigate from collection to viewable images:

```python
from idc_index import IDCClient

client = IDCClient.client()

# Get patients in a collection
patients = client.get_patients("tcga_luad", outputFormat="list")
print(f"Found {len(patients)} patients")

# Get studies for a patient
studies = client.get_dicom_studies(patients[0])

# Get series in that study
series = client.get_dicom_series(studies[0]["StudyInstanceUID"])

# Generate a viewer URL
viewer_url = client.get_viewer_URL(seriesInstanceUID=series[0]["SeriesInstanceUID"])
print(f"View in browser: {viewer_url}")
```

## Command Line Interface

Download data directly from the terminal using `idc download`, which
auto-detects the input type:

```bash
# Download a collection
idc download rider_pilot

# Download a specific series by UID
idc download 1.3.6.1.4.1.14519.5.2.1.6279.6001.100225287222365663678666836860

# Download from a manifest file
idc download manifest.s5cmd

# Specify output directory
idc download rider_pilot --download-dir ./data

# See all options
idc --help
```

## Documentation

- [**Full Documentation**](https://idc-index.readthedocs.io) - API reference and
  guides
- [**Tutorial Notebook**](https://github.com/ImagingDataCommons/IDC-Tutorials/blob/master/notebooks/labs/idc_rsna2023.ipynb) -
  Interactive introduction to idc-index

## Resources

- [IDC Portal](https://imaging.datacommons.cancer.gov/) - Browse IDC data in
  your web browser
- [IDC Forum](https://discourse.canceridc.dev/) - Community discussions and
  support
- [idc-claude-skill](https://github.com/ImagingDataCommons/idc-claude-skill) -
  Claude AI skill for querying IDC with natural language
- [SlicerIDCBrowser](https://github.com/ImagingDataCommons/SlicerIDCBrowser) -
  3D Slicer extension using idc-index
- [s5cmd](https://github.com/peak/s5cmd) - The high-performance S3 client
  powering downloads

## Citation

If idc-index helps your research, please cite:

> Fedorov, A., Longabaugh, W. J. R., Pot, D., Clunie, D. A., Pieper, S. D.,
> Gibbs, D. L., Bridge, C., Herrmann, M. D., Homeyer, A., Lewis, R., Aerts, H.
> J. W., Krishnaswamy, D., Thiriveedhi, V. K., Ciausu, C., Schacherer, D. P.,
> Bontempi, D., Pihl, T., Wagner, U., Farahani, K., Kim, E. & Kikinis, R.
> _National Cancer Institute Imaging Data Commons: Toward Transparency,
> Reproducibility, and Scalability in Imaging Artificial Intelligence_.
> RadioGraphics (2023). https://doi.org/10.1148/rg.230180

## Acknowledgment

This software is maintained by the IDC team, which has been funded in whole or
in part with Federal funds from the NCI, NIH, under task order no. HHSN26110071
under contract no. HHSN261201500003I.

<!-- prettier-ignore-start -->
[actions-badge]:            https://github.com/ImagingDataCommons/idc-index/workflows/CI/badge.svg
[actions-link]:             https://github.com/ImagingDataCommons/idc-index/actions
[discourse-forum-badge]: https://img.shields.io/discourse/https/discourse.canceridc.dev/status.svg
[discourse-forum-link]:  https://discourse.canceridc.dev/
[pypi-link]:                https://pypi.org/project/idc-index/
[pypi-platforms]:           https://img.shields.io/pypi/pyversions/idc-index
[pypi-version]:             https://img.shields.io/pypi/v/idc-index
[rtd-badge]:                https://readthedocs.org/projects/idc-index/badge/?version=latest
[rtd-link]:                 https://idc-index.readthedocs.io/en/latest/?badge=latest

<!-- prettier-ignore-end -->
