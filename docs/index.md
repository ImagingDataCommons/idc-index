<h1 align="center" style="font-size: 3rem; margin: -15px 0">
idc-index
</h1>

---

`idc-index` is a lightweight Python package to support interaction with [NCI Imaging Data Commons](https://imaging.datacommons.cancer.gov)

Install `idc-index` using pip:

```shell
$ pip install idc-index
```

```pycon
from idc_index import index

client = index.IDCClient()

client.download_from_selection(collection_id = 'rider_pilot', downloadDir = '/some/dir')
```

... or run queries against the "mini" index of Imaging Data Commons data! 
```pycon
from idc_index import index

client = index.IDCClient()

query = """
SELECT
  collection_id,
  STRING_AGG(DISTINCT(Modality)) as modalities,
  STRING_AGG(DISTINCT(BodyPartExamined)) as body_parts
FROM
  index
GROUP BY
  collection_id
ORDER BY
  collection_id ASC
"""

client.sql_query(query)
```

Details of the attributes included in the index are in the release notes.

## Tutorial

This package was first presented at the 2023 Annual meeting of Radiological Society of North America (RSNA) Deep Learning Lab [IDC session](https://github.com/RSNA/AI-Deep-Learning-Lab-2023/tree/main/sessions/idc).

Please check out [this tutorial notebook](https://github.com/ImagingDataCommons/IDC-Tutorials/blob/master/notebooks/labs/idc_rsna2023.ipynb) for the introduction into using `idc-index` for navigating IDC data.

## Resources

* [Imaging Data Commons Portal](https://imaging.datacommons.cancer.gov/) can be used to explore the content of IDC from the web browser
* [s5cmd](https://github.com/peak/s5cmd) is a highly efficient, open source, multi-platform S3 client that we use for downloading IDC data, which is hosted in public AWS and GCS buckets
* [SlicerIDCBrowser](https://github.com/ImagingDataCommons/SlicerIDCBrowser) 3D Slicer extension that relies on `idc-index` for search and download of IDC data

## Acknowledgment

This software is maintained by the IDC team, which has been funded in whole or in part with Federal funds from the NCI, NIH, under task order no. HHSN26110071 under contract no. HHSN261201500003l.

If this package helped your research, we would appreciate if you could cite IDC paper below.

> Fedorov, A., Longabaugh, W. J. R., Pot, D., Clunie, D. A., Pieper, S. D., Gibbs, D. L., Bridge, C., Herrmann, M. D., Homeyer, A., Lewis, R., Aerts, H. J. W., Krishnaswamy, D., Thiriveedhi, V. K., Ciausu, C., Schacherer, D. P., Bontempi, D., Pihl, T., Wagner, U., Farahani, K., Kim, E. & Kikinis, R. _National Cancer Institute Imaging Data Commons: Toward Transparency, Reproducibility, and Scalability in Imaging Artificial Intelligence_. RadioGraphics (2023). https://doi.org/10.1148/rg.230180