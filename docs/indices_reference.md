# Index Tables Reference

This page provides a comprehensive reference for all index tables available in
`idc-index`. The documentation is automatically generated from the schemas
provided by `idc-index-data`.

> **Note:** Column descriptions are sourced directly from the `idc-index-data`
> package schemas. If you notice any missing or incorrect descriptions, please
> report them in the
> [idc-index-data repository](https://github.com/ImagingDataCommons/idc-index-data).

## Overview

`idc-index` provides access to multiple index tables containing metadata about
the files available in IDC. Each table serves a specific purpose and contains
different metadata attributes.

## Table Relationships

The following diagram shows how the different index tables relate to each other
based on shared column names:

```{mermaid}
:zoom:

erDiagram
    analysis_results_index {
        STRING analysis_result_id
        STRING analysis_result_title
        STRING source_doi
        STRING source_url
        INTEGER Subjects
        STRING Collections
        STRING AnalysisArtifacts
        DATE Updated
        STRING license_url
        STRING license_long_name
        STRING license_short_name
        STRING Description
        STRING Citation
    }
    clinical_index {
        STRING collection_id
        STRING table_name
        STRING short_table_name
        STRING column
        STRING column_label
        RECORD values
    }
    collections_index {
        STRING collection_name
        STRING collection_id
        STRING CancerTypes
        STRING TumorLocations
        INTEGER Subjects
        STRING Species
        RECORD Sources
        STRING SupportingData
        STRING Program
        STRING Status
        DATE Updated
        STRING Description
    }
    index {
        STRING collection_id
        STRING analysis_result_id
        STRING PatientID
        STRING SeriesInstanceUID
        STRING StudyInstanceUID
        STRING source_DOI
        STRING PatientAge
        STRING PatientSex
        DATE StudyDate
        STRING StudyDescription
        STRING BodyPartExamined
        STRING Modality
        STRING Manufacturer
        STRING ManufacturerModelName
        STRING SeriesDate
        STRING SeriesDescription
        STRING SeriesNumber
        INTEGER instanceCount
        STRING license_short_name
        STRING aws_bucket
        STRING crdc_series_uuid
        STRING series_aws_url
        FLOAT series_size_MB
    }
    prior_versions_index {
        STRING collection_id
        STRING PatientID
        STRING SeriesInstanceUID
        STRING StudyInstanceUID
        STRING Modality
        STRING gcs_bucket
        STRING crdc_series_uuid
        FLOAT series_size_MB
        STRING series_aws_url
        STRING gcs_bucket_1
        STRING aws_bucket
        INTEGER min_idc_version
        INTEGER max_idc_version
    }
    sm_index {
        STRING SeriesInstanceUID
        STRING embeddingMedium_CodeMeaning
        STRING embeddingMedium_code_designator_value_str
        STRING tissueFixative_CodeMeaning
        STRING tissueFixative_code_designator_value_str
        STRING staining_usingSubstance_CodeMeaning
        STRING staining_usingSubstance_code_designator_value_str
        FLOAT min_PixelSpacing_2sf
        INTEGER max_TotalPixelMatrixColumns
        INTEGER max_TotalPixelMatrixRows
        INTEGER ObjectiveLensPower
        STRING primaryAnatomicStructure_code_designator_value_str
        STRING primaryAnatomicStructure_CodeMeaning
        STRING primaryAnatomicStructureModifier_code_designator_value_str
        STRING primaryAnatomicStructureModifier_CodeMeaning
        STRING illuminationType_code_designator_value_str
        STRING illuminationType_CodeMeaning
        STRING admittingDiagnosis_code_designator_value_str
        STRING admittingDiagnosis_CodeMeaning
    }
    sm_instance_index {
        STRING SOPInstanceUID
        STRING SeriesInstanceUID
        STRING embeddingMedium_CodeMeaning
        STRING embeddingMedium_code_designator_value_str
        STRING tissueFixative_CodeMeaning
        STRING tissueFixative_code_designator_value_str
        STRING staining_usingSubstance_CodeMeaning
        STRING staining_usingSubstance_code_designator_value_str
        FLOAT PixelSpacing_0
        STRING ImageType
        STRING TransferSyntaxUID
        INTEGER instance_size
        INTEGER TotalPixelMatrixColumns
        INTEGER TotalPixelMatrixRows
        STRING crdc_instance_uuid
    }
    clinical_index ||--o{ collections_index : collection_id
    clinical_index ||--o{ index : collection_id
    clinical_index ||--o{ prior_versions_index : collection_id
    collections_index ||--o{ index : collection_id
    collections_index ||--o{ prior_versions_index : collection_id
    index ||--o{ prior_versions_index : collection_id
    index ||--o{ prior_versions_index : SeriesInstanceUID
    index ||--o{ prior_versions_index : crdc_series_uuid
    index ||--o{ prior_versions_index : PatientID
    index ||--o{ prior_versions_index : StudyInstanceUID
    index ||--o{ sm_index : SeriesInstanceUID
    index ||--o{ sm_instance_index : SeriesInstanceUID
    prior_versions_index ||--o{ sm_index : SeriesInstanceUID
    prior_versions_index ||--o{ sm_instance_index : SeriesInstanceUID
    sm_index ||--o{ sm_instance_index : SeriesInstanceUID
```

## Available Index Tables

## `index`

This is the main metadata table provided by idc-index. Each row corresponds to a
DICOM series, and contains attributes at the collection, patient, study, and
series levels. The table also contains download-related attributes, such as the
AWS S3 bucket and URL to download the series.

### Columns

- **`collection_id`** (`STRING`, NULLABLE): short string with the identifier of
  the collection the series belongs to
- **`analysis_result_id`** (`STRING`, NULLABLE): this string is not empty if the
  specific series is part of an analysis results collection; analysis results
  can be added to a given collection over time
- **`PatientID`** (`STRING`, NULLABLE): identifier of the patient within the
  collection (DICOM attribute)
- **`SeriesInstanceUID`** (`STRING`, NULLABLE): unique identifier of the DICOM
  series (DICOM attribute)
- **`StudyInstanceUID`** (`STRING`, NULLABLE): unique identifier of the DICOM
  study (DICOM attribute)
- **`source_DOI`** (`STRING`, NULLABLE): Digital Object Identifier of the
  dataset that contains the given series; follow this DOI to learn more about
  the activity that produced this series
- **`PatientAge`** (`STRING`, NULLABLE): age of the subject at the time of
  imaging (DICOM attribute)
- **`PatientSex`** (`STRING`, NULLABLE): subject sex (DICOM attribute)
- **`StudyDate`** (`DATE`, NULLABLE): date of the study (de-identified) (DICOM
  attribute)
- **`StudyDescription`** (`STRING`, NULLABLE): textual description of the study
  content (DICOM attribute)
- **`BodyPartExamined`** (`STRING`, NULLABLE): body part imaged (not
  iniapplicabletialized for SM series) (DICOM attribute)
- **`Modality`** (`STRING`, NULLABLE): acquisition modality (DICOM attribute)
- **`Manufacturer`** (`STRING`, NULLABLE): manufacturer of the equipment that
  produced the series (DICOM attribute)
- **`ManufacturerModelName`** (`STRING`, NULLABLE): model name of the equipment
  that produced the series (DICOM attribute)
- **`SeriesDate`** (`STRING`, NULLABLE): date of the series (de-identified)
  (DICOM attribute)
- **`SeriesDescription`** (`STRING`, NULLABLE): textual description of the
  series content (DICOM attribute)
- **`SeriesNumber`** (`STRING`, NULLABLE): series number (DICOM attribute)
- **`instanceCount`** (`INTEGER`, NULLABLE): number of instances in the series
- **`license_short_name`** (`STRING`, NULLABLE): short name of the license that
  applies to this series
- **`aws_bucket`** (`STRING`, NULLABLE): name of the AWS S3 bucket that contains
  the series
- **`crdc_series_uuid`** (`STRING`, NULLABLE): unique identifier of the series
  within the IDC
- **`series_aws_url`** (`STRING`, NULLABLE): public AWS S3 URL to download the
  series in bulk (each instance is a separate file)
- **`series_size_MB`** (`FLOAT`, NULLABLE): total size of the series in
  megabytes

## `prior_versions_index`

### Columns

- **`collection_id`** (`STRING`, NULLABLE):
- **`PatientID`** (`STRING`, NULLABLE):
- **`SeriesInstanceUID`** (`STRING`, NULLABLE):
- **`StudyInstanceUID`** (`STRING`, NULLABLE):
- **`Modality`** (`STRING`, NULLABLE):
- **`gcs_bucket`** (`STRING`, NULLABLE):
- **`crdc_series_uuid`** (`STRING`, NULLABLE):
- **`series_size_MB`** (`FLOAT`, NULLABLE):
- **`series_aws_url`** (`STRING`, NULLABLE):
- **`gcs_bucket_1`** (`STRING`, NULLABLE):
- **`aws_bucket`** (`STRING`, NULLABLE):
- **`min_idc_version`** (`INTEGER`, NULLABLE):
- **`max_idc_version`** (`INTEGER`, NULLABLE):

## `analysis_results_index`

This table contains metadata about the analysis results collections available in
IDC. Each row corresponds to an analysis results collection, and contains
attributes such as the collection name, types of cancer represented, number of
subjects, and pointers to the resources to learn more about the content of the
collection

### Columns

- **`analysis_result_id`** (`STRING`, NULLABLE): unique identifier of the
  analysis results collection
- **`analysis_result_title`** (`STRING`, NULLABLE): name of the analysis results
  collection
- **`source_doi`** (`STRING`, NULLABLE): Digital Object Identifier (DOI) of the
  analysis results collection
- **`source_url`** (`STRING`, NULLABLE): URL for the location of additional
  information about the analysis results collection
- **`Subjects`** (`INTEGER`, NULLABLE): number of subjects analyzed in the
  analysis results collection
- **`Collections`** (`STRING`, NULLABLE): collections analyzed in the analysis
  results collection
- **`AnalysisArtifacts`** (`STRING`, NULLABLE): analysis artifacts included in
  the analysis results collection
- **`Updated`** (`DATE`, NULLABLE): timestamp of the last update to the analysis
  results collection
- **`license_url`** (`STRING`, NULLABLE): license URL for the analysis results
  collection
- **`license_long_name`** (`STRING`, NULLABLE): license name for the analysis
  results collection
- **`license_short_name`** (`STRING`, NULLABLE): short name for the license of
  the analysis results collection
- **`Description`** (`STRING`, NULLABLE): detailed description of the analysis
  results collection
- **`Citation`** (`STRING`, NULLABLE): citation for the analysis results
  collection that should be used for acknowledgment

## `clinical_index`

This table contains metadata about the tabular data, including clinical data,
accompanying images that is available in IDC. Think about this table as a
dictionary containing information about the columns for all of the tabular data
accompanying individual collections in IDC. Each row corresponds to a unique
combination of collection, clinical data table that is available for that
collection, and a column from that table. Individual tables referenced from this
table can be retrieved using idc-index `get_clinical_table()` function.

### Columns

- **`collection_id`** (`STRING`, NULLABLE): unique identifier of the collection
- **`table_name`** (`STRING`, NULLABLE): full name of the table in which the
  column is stored
- **`short_table_name`** (`STRING`, NULLABLE): short name of the table in which
  the column is stored
- **`column`** (`STRING`, NULLABLE):
- **`column_label`** (`STRING`, NULLABLE): human readable name of the column
- **`values`** (`RECORD`, REPEATED):

## `collections_index`

This table contains metadata about the collections available in IDC. Each row
corresponds to a collection, and contains attributes such as the collection
name, types of cancer represented, number of subjects, and pointers to the
resources to learn more about the content of the collection.

### Columns

- **`collection_name`** (`STRING`, NULLABLE): name of the collection
- **`collection_id`** (`STRING`, NULLABLE): unique identifier of the collection
- **`CancerTypes`** (`STRING`, NULLABLE): types of cancer represented in the
  collection
- **`TumorLocations`** (`STRING`, NULLABLE): locations of tumors represented in
  the collection
- **`Subjects`** (`INTEGER`, NULLABLE): number of subjects in the collection
- **`Species`** (`STRING`, NULLABLE): species represented in the collection
- **`Sources`** (`RECORD`, REPEATED): sources of data for the collection
- **`SupportingData`** (`STRING`, NULLABLE): additional data supporting the
  collection available in IDC
- **`Program`** (`STRING`, NULLABLE): broader initiative/category under which
  this collection is being shared
- **`Status`** (`STRING`, NULLABLE): status of the collection (Completed or
  Ongoing)
- **`Updated`** (`DATE`, NULLABLE): timestamp of the last update to the
  collection
- **`Description`** (`STRING`, NULLABLE): detailed information about the
  collection

## `sm_index`

This table contains metadata about the slide microscopy (SM) series available in
IDC. Each row corresponds to a DICOM series, and contains attributes specific to
SM series, such as the pixel spacing at the maximum resolution layer, the power
of the objective lens used to digitize the slide, and the anatomic location from
where the imaged specimen was collected. This table can be joined with the main
index table using the `SeriesInstanceUID` column.

### Columns

- **`SeriesInstanceUID`** (`STRING`, NULLABLE):
- **`embeddingMedium_CodeMeaning`** (`STRING`, REPEATED): embedding medium used
  for the slide preparation
- **`embeddingMedium_code_designator_value_str`** (`STRING`, REPEATED):
  embedding medium code tuple
- **`tissueFixative_CodeMeaning`** (`STRING`, REPEATED): tissue fixative used
  for the slide preparation
- **`tissueFixative_code_designator_value_str`** (`STRING`, REPEATED): tissue
  fixative code tuple
- **`staining_usingSubstance_CodeMeaning`** (`STRING`, REPEATED): staining
  substances used for the slide preparation
- **`staining_usingSubstance_code_designator_value_str`** (`STRING`, REPEATED):
  staining using substance code tuple
- **`min_PixelSpacing_2sf`** (`FLOAT`, NULLABLE): pixel spacing in mm at the
  maximum resolution layer, rounded to 2 significant figures
- **`max_TotalPixelMatrixColumns`** (`INTEGER`, NULLABLE): width of the image at
  the maximum resolution
- **`max_TotalPixelMatrixRows`** (`INTEGER`, NULLABLE): height of the image at
  the maximum resolution
- **`ObjectiveLensPower`** (`INTEGER`, NULLABLE): power of the objective lens of
  the equipment used to digitize the slide
- **`primaryAnatomicStructure_code_designator_value_str`** (`STRING`, NULLABLE):
  anatomic location from where the imaged specimen was collected
- **`primaryAnatomicStructure_CodeMeaning`** (`STRING`, NULLABLE): code tuple
  for the anatomic location from where the imaged specimen was collected
- **`primaryAnatomicStructureModifier_code_designator_value_str`** (`STRING`,
  NULLABLE): additional characteristics of the specimen, such as whether it is a
  tumor or normal tissue (when available)
- **`primaryAnatomicStructureModifier_CodeMeaning`** (`STRING`, NULLABLE): code
  tuple for additional characteristics of the specimen, such as whether it is a
  tumor or normal tissue (when available)
- **`illuminationType_code_designator_value_str`** (`STRING`, NULLABLE):
  illumination type used during slide digitization
- **`illuminationType_CodeMeaning`** (`STRING`, NULLABLE): code tuple for the
  illumination type used during slide digitization
- **`admittingDiagnosis_code_designator_value_str`** (`STRING`, NULLABLE):
  admitting diagnosis associated with the specimen imaged on the slide (when
  available)
- **`admittingDiagnosis_CodeMeaning`** (`STRING`, NULLABLE): code tuple for the
  admitting diagnosis associated with the specimen imaged on the slide (when
  available)

## `sm_instance_index`

This table contains metadata about the slide microscopy (SM) series available in
IDC. Each row corresponds to an instance from a DICOM Slide Microscopy series
available from IDC, identified by `SOPInstanceUID`, and contains attributes
specific to SM series, such as the pixel spacing at the maximum resolution
layer, the power of the objective lens used to digitize the slide, and the
anatomic location from where the imaged specimen was collected. This table can
be joined with the main index table and/or with `sm_index` using the
`SeriesInstanceUID` column.

### Columns

- **`SOPInstanceUID`** (`STRING`, NULLABLE): unique identifier of the instance
- **`SeriesInstanceUID`** (`STRING`, NULLABLE): unique identifier of the series
- **`embeddingMedium_CodeMeaning`** (`STRING`, REPEATED): embedding medium used
  for the slide preparation
- **`embeddingMedium_code_designator_value_str`** (`STRING`, REPEATED):
  embedding medium code tuple
- **`tissueFixative_CodeMeaning`** (`STRING`, REPEATED): tissue fixative used
  for the slide preparation
- **`tissueFixative_code_designator_value_str`** (`STRING`, REPEATED): tissue
  fixative code tuple
- **`staining_usingSubstance_CodeMeaning`** (`STRING`, REPEATED): staining
  substances used for the slide preparation
- **`staining_usingSubstance_code_designator_value_str`** (`STRING`, REPEATED):
  staining using substance code tuple
- **`PixelSpacing_0`** (`FLOAT`, NULLABLE): pixel spacing in mm, rounded to 2
  significant figures
- **`ImageType`** (`STRING`, REPEATED): DICOM ImageType attribute
- **`TransferSyntaxUID`** (`STRING`, NULLABLE): DICOM TransferSyntaxUID
  attribute
- **`instance_size`** (`INTEGER`, NULLABLE): size of the instance file in bytes
- **`TotalPixelMatrixColumns`** (`INTEGER`, NULLABLE): number of columns in the
  image
- **`TotalPixelMatrixRows`** (`INTEGER`, NULLABLE): number of rows in the image
- **`crdc_instance_uuid`** (`STRING`, NULLABLE): unique identifier of the
  instance within the IDC
