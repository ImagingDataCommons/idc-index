# idc-index

```{toctree}
:maxdepth: 2
:hidden:
```

:::{warning}

This package is in its early development stages. Its functionality and API will
change.

Stay tuned for the updates and documentation, and please share your feedback
about it by opening issues at the
[idc-index](https://github.com/ImagingDataCommons/idc-index) repository, or by
starting a discussion in [IDC User forum](https://discourse.canceridc.dev/).

:::

```{include} ../README.md
:start-after: <!-- SPHINX-START -->
```

## The `index` of `idc-index`

`idc-index` is named this way because it wraps index of IDC data: a table
containing most important metadata attributes describing the files available in
IDC. This metadata index is available in the `index` variable (which is a pandas
`DataFrame`) of `IDCClient`.

The following is the list of the columns included in `index`. You can use those
to select cohorts and subsetting data. `idc-index` is series-based, i.e, it has
one row per DICOM series.

- non-DICOM attributes assigned/curated by IDC:

  - `collection_id`: short string with the identifier of the collection the
    series belongs to
  - `analysis_result_id`: this string is not empty if the specific series is
    part of an analysis results collection; analysis results can be added to a
    given collection over time
  - `source_DOI`: Digital Object Identifier of the dataset that contains the
    given series; note that a given collection can include one or more DOIs,
    since analysis results added to the collection would typically have
    independent DOI values!
  - `instanceCount`: number of files in the series (typically, this matches the
    number of slices in cross-sectional modalities)
  - `license_short_name`: short name of the license that governs the use of the
    files corresponding to the series
  - `series_aws_url`: location of the series files in a public AWS bucket
  - `series_size_MB`: total disk size needed to store the series

- DICOM attributes extracted from the files
  - `PatientID`: identifier of the patient
  - `PatientAge` and `PatientSex`: attributes containing patient age and sex
  - `StudyInstanceUID`: unique identifier of the DICOM study
  - `StudyDescription`: textual description of the study content
  - `StudyDate`: date of the study (note that those dates are shifted, and are
    not real dates when images were acquired, to protect patient privacy)
  - `SeriesInstanceUID`: unique identifier of the DICOM series
  - `SeriesDate`: date when the series was acquired
  - `SeriesDescription`: textual description of the series content
  - `SeriesNumber`: series number
  - `BodyPartExamined`: body part imaged
  - `Modality`: acquisition modality
  - `Manufacturer`: manufacturer of the equipment that generated the series
  - `ManufacturerModelName`: model name of the equipment

## Contents

```{toctree}
:maxdepth: 1
:titlesonly:
:caption: API docs

api/idc_index
```

## Indices and tables

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`
