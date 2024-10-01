# idc-index

[![Actions Status][actions-badge]][actions-link]
[![Documentation Status][rtd-badge]][rtd-link]

[![PyPI version][pypi-version]][pypi-link]
[![PyPI platforms][pypi-platforms]][pypi-link]

[![Discourse Forum][discourse-forum-badge]][discourse-forum-link]

> [!WARNING]
>
> This package is in its early development stages. Its functionality and API
> will change.
>
> Stay tuned for the updates and documentation, and please share your feedback
> about it by opening issues in this repository, or by starting a discussion in
> [IDC User forum](https://discourse.canceridc.dev/).

<!-- SPHINX-START -->

## About

`idc-index` is a Python package that enables basic operations for working with
[NCI Imaging Data Commons (IDC)](https://imaging.datacommons.cancer.gov):

- subsetting of the IDC data using selected metadata attributes
- download of the files corresponding to selection
- generation of the viewer URLs for the selected data

## Getting started

Install the latest version of the package.

```bash
$ pip install --upgrade idc-index
```

Instantiate `IDCClient`, which provides the interface for main operations.

```python
from idc_index import IDCClient

client = IDCClient.client()
```

You can use [IDC Portal](https://imaging.datacommons.cancer.gov/explore) to
browse collections, cases, studies and series, copy their identifiers and
download the corresponding files using `idc-index` helper functions.

You can try this out with the `rider_pilot` collection, which is just 10.5 GB in
size:

```
client.download_from_selection(collection_id="rider_pilot", downloadDir=".")
```

... or run queries against the "mini" index of Imaging Data Commons data, and
download images that match your selection criteria! The following will select
all Magnetic Resonance (MR) series, and will download the first 10.

```python
from idc_index import index

client = index.IDCClient()

query = """
SELECT
  SeriesInstanceUID
FROM
  index
WHERE
  Modality = 'MR'
"""

selection_df = client.sql_query(query)

client.download_from_selection(
    seriesInstanceUID=list(selection_df["SeriesInstanceUID"].values[:10]),
    downloadDir=".",
)
```

## The `indices` of `idc-index`

`idc-index` is named this way because it wraps indices of IDC data: tables
containing the most important metadata attributes describing the files available
in IDC. The main metadata index is available in the `index` variable (which is a
pandas `DataFrame`) of `IDCClient`. Additional index tables such as the
`clinical_index` contain non-DICOM clinical data or slide microscopy specific
tables (indicated by the prefix `sm`) include metadata attributes specific to
slide microscopy images. A description of available attributes for all indices
can be found [here](column_descriptions).

## Tutorial

Please check out
[this tutorial notebook](https://github.com/ImagingDataCommons/IDC-Tutorials/blob/master/notebooks/labs/idc_rsna2023.ipynb)
for the introduction into using `idc-index`.

## Resources

- [Imaging Data Commons Portal](https://imaging.datacommons.cancer.gov/) can be
  used to explore the content of IDC from the web browser
- [s5cmd](https://github.com/peak/s5cmd) is a highly efficient, open source,
  multi-platform S3 client that we use for downloading IDC data, which is hosted
  in public AWS and GCS buckets. Distributed on PyPI as
  [s5cmd](https://pypi.org/project/s5cmd/).
- [SlicerIDCBrowser](https://github.com/ImagingDataCommons/SlicerIDCBrowser) 3D
  Slicer extension that relies on `idc-index` for search and download of IDC
  data

## Acknowledgment

This software is maintained by the IDC team, which has been funded in whole or
in part with Federal funds from the NCI, NIH, under task order no. HHSN26110071
under contract no. HHSN261201500003l.

If this package helped your research, we would appreciate if you could cite IDC
paper below.

> Fedorov, A., Longabaugh, W. J. R., Pot, D., Clunie, D. A., Pieper, S. D.,
> Gibbs, D. L., Bridge, C., Herrmann, M. D., Homeyer, A., Lewis, R., Aerts, H.
> J. W., Krishnaswamy, D., Thiriveedhi, V. K., Ciausu, C., Schacherer, D. P.,
> Bontempi, D., Pihl, T., Wagner, U., Farahani, K., Kim, E. & Kikinis, R.
> _National Cancer Institute Imaging Data Commons: Toward Transparency,
> Reproducibility, and Scalability in Imaging Artificial Intelligence_.
> RadioGraphics (2023). https://doi.org/10.1148/rg.230180

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
