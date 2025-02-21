# Metadata attributes in `idc-index`'s index tables

`idc-index` is named this way because it wraps indices of IDC data: tables
containing the most important metadata attributes describing the files available
in IDC. The main metadata index is available in the `index` variable (which is a
pandas `DataFrame`) of `IDCClient`. Additional index tables such as the
`clinical_index` contain non-DICOM clinical data or slide microscopy specific
tables (indicated by the prefix `sm`) include metadata attributes specific to
slide microscopy images.

## `index`

The following is the list of the columns included in `index`. You can use those
to select cohorts and subsetting data. `index` is series-based, i.e, it has one
row per DICOM series.

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

## `sm_index`

The following is the list of the columns included in `sm_index`. `sm_index` is
series-based, i.e, it has one row per DICOM series, but only includes series
with slide microscopy data.

- DICOM attributes extracted from the files:
  - `SeriesInstanceUID`: unique identifier of the DICOM series: one DICOM series
    = one slide
  - `embeddingMedium`: describes in what medium the slide was embedded before
    the image was obtained
  - `tissueFixative`: describes tissue fixatives used before the image was
    obtained
  - `staining_usingSubstance`: describes staining steps the specimen underwent
    before the image was obtained
  - `max_TotalPixelMatrixColumns`: width of the image at the maximum resolution
  - `max_TotalMatrixRows`: height of the image at the maximum resolution
  - `min_PixelSpacing_2sf`: pixel spacing in mm at the maximum resolution layer,
    rounded to 2 significant figures
  - `ObjectiveLensPower`: power of the objective lens of the equipment used to
    digitize the slide
  - `primaryAnatomicStructure`: anatomic location from where the imaged specimen
    was collected
  - `primaryAnatomicStructureModifier`: additional characteristics of the
    specimen, such as whether it is a tumor or normal tissue
  - `admittingDiagnosis`: if available, diagnosis of the patient; populated
    using the first item of the `AdmittingDiagnosesSequence` in DICOM SM series
  - `illuminationType`: specifies the type of illumination used when obtaining
    the image

In case of `embeddingMedium`, `tissueFixative`, `staining_usingSubstance`,
`primaryAnatomicStructure`, `primaryAnatomicStructureModifier`,
`admittingDiagnosis` and `illuminationType` the attributes exist with suffix
`_code_designator_value_str` and `_CodeMeaning`, which indicates whether the
column contains CodeSchemeDesignator and CodeValue, or CodeMeaning. If this is
new to you, a brief explanation on the three-value based coding scheme in DICOM
can be found at https://learn.canceridc.dev/dicom/coding-schemes.

## `sm_instance_index`

The following is the list of the columns included in `sm_instance_index`.
`sm_instance_index` is instance-based, i.e, it has one row per DICOM instance
(pyramid level of a slide, plus potentially thumbnail or label images), but only
includes DICOM instances of the slide microscopy modality.

- DICOM attributes extracted from the files:

  - `SOPInstanceUID`: unique identifier of the DICOM instance: one DICOM
    instance = one level/label/thumbnail image of the slide
  - `SeriesInstanceUID`: unique identifier of the DICOM series: one DICOM series
    = one slide
  - `embeddingMedium`: describes in what medium the slide was embedded before
    the image was obtained
  - `tissueFixative`: describes tissue fixatives used before the image was
    obtained
  - `staining_usingSubstance`: describes staining steps the specimen underwent
    before the image was obtained
  - `max_TotalPixelMatrixColumns`: width of the image at the maximum resolution
  - `max_TotalMatrixRows`: height of the image at the maximum resolution
  - `PixelSpacing_0`: pixel spacing in mm
  - `ImageType`: specifies further characteristics of the image in a list,
    including as the third value whether it is a VOLUME, LABEL, OVERVIEW or
    THUMBNAIL image.
  - `TransferSyntaxUID`: specifies the encoding scheme used for the image data
  - `instance_size`: specifies the DICOM instance's size in bytes

- non-DICOM attributes assigned/curated by IDC:
  - `crdc_instance_uuid`: globally unique, versioned identifier of the DICOM
    instance

In case of `embeddingMedium`, `tissueFixative`, and `staining_usingSubstance`
the attributes exist with suffix `_code_designator_value_str` and
`_CodeMeaning`, which indicates whether the column contains CodeSchemeDesignator
and CodeValue, or CodeMeaning. If this is new to you, a brief explanation on the
three-value based coding scheme in DICOM can be found at
https://learn.canceridc.dev/dicom/coding-schemes.

## `clinical_index`

Many of the image collections available in IDC are accompanied by clinical data.
Such clinical data is organized in one or more tables that are shared alongside
the images.

Each row in `clinical_index` corresponds to a column in a clinical table
available in IDC. You can use this index to find collections that have a
specific clinical attribute, compare availability of the clinical data across
collections, identify patients that have specific clinical characteristics.

Note that IDC does not perform any harmonization of the clinical data across
collections, or any validation of the content of the tables. We share clinical
data as it was provided by the submitter.

provides the list of all of the columns across all of the clinical tables
available in IDC. It contains the following items:

- `collection_id`: identifier of the collection where the given clinical data
  attribute is available
- `short_table_name`: name of the clinical data table where the attribute is
  encountered; the referenced table can be loaded into a Pandas DataFrame using
  the `IDCClient.get_clinical_data()` call
- `table_name`: fully resolved name of the table in IDC Google BigQuery public
  dataset (only relevant if you would like to search using BigQuery)
- `column`: name of the column that is available in the given clinical table
- `colum_label`: label of the column (this field may contain more extensive
  information describing a given column)
- `values`: set of values defining the content of the column (relevant if the
  column contains fixed list of values and not free text)
