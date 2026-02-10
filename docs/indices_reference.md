# Index Tables Reference

This page provides a comprehensive reference for all index tables available in
`idc-index`. The documentation is automatically generated from the schemas
provided by `idc-index-data` (version 23.5.0).

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
based on shared key columns. Only key columns used for joins are shown in the
diagram; see the individual table sections below for complete column lists.

```{mermaid}
:zoom:

erDiagram
    analysis_results_index {
        STRING analysis_result_id
        STRING source_DOI
    }
    ann_group_index {
        STRING SeriesInstanceUID
    }
    ann_index {
        STRING SeriesInstanceUID
    }
    clinical_index {
        STRING collection_id
    }
    collections_index {
        STRING collection_id
    }
    contrast_index {
        STRING SeriesInstanceUID
    }
    index {
        STRING PatientID
        STRING SeriesInstanceUID
        STRING StudyInstanceUID
        STRING analysis_result_id
        STRING collection_id
        STRING crdc_series_uuid
        STRING source_DOI
    }
    prior_versions_index {
        STRING PatientID
        STRING SeriesInstanceUID
        STRING StudyInstanceUID
        STRING collection_id
        STRING crdc_series_uuid
    }
    seg_index {
        STRING SeriesInstanceUID
    }
    sm_index {
        STRING SeriesInstanceUID
    }
    sm_instance_index {
        STRING SOPInstanceUID
        STRING SeriesInstanceUID
    }
    index ||--o{ prior_versions_index : PatientID
    index ||--o{ prior_versions_index : SeriesInstanceUID
    index ||--o{ prior_versions_index : StudyInstanceUID
    index ||--o{ prior_versions_index : collection_id
    index ||--o{ prior_versions_index : crdc_series_uuid
    index ||--o{ collections_index : collection_id
    index ||--o{ analysis_results_index : analysis_result_id
    index ||--o{ analysis_results_index : source_DOI
    index ||--o{ clinical_index : collection_id
    index ||--o{ sm_index : SeriesInstanceUID
    index ||--o{ sm_instance_index : SeriesInstanceUID
    index ||--o{ seg_index : SeriesInstanceUID
    index ||--o{ ann_index : SeriesInstanceUID
    index ||--o{ ann_group_index : SeriesInstanceUID
    index ||--o{ contrast_index : SeriesInstanceUID
    prior_versions_index ||--o{ collections_index : collection_id
    prior_versions_index ||--o{ clinical_index : collection_id
    prior_versions_index ||--o{ sm_index : SeriesInstanceUID
    prior_versions_index ||--o{ sm_instance_index : SeriesInstanceUID
    prior_versions_index ||--o{ seg_index : SeriesInstanceUID
    prior_versions_index ||--o{ ann_index : SeriesInstanceUID
    prior_versions_index ||--o{ ann_group_index : SeriesInstanceUID
    prior_versions_index ||--o{ contrast_index : SeriesInstanceUID
    collections_index ||--o{ clinical_index : collection_id
    sm_index ||--o{ sm_instance_index : SeriesInstanceUID
    sm_index ||--o{ seg_index : SeriesInstanceUID
    sm_index ||--o{ ann_index : SeriesInstanceUID
    sm_index ||--o{ ann_group_index : SeriesInstanceUID
    sm_index ||--o{ contrast_index : SeriesInstanceUID
    sm_instance_index ||--o{ seg_index : SeriesInstanceUID
    sm_instance_index ||--o{ ann_index : SeriesInstanceUID
    sm_instance_index ||--o{ ann_group_index : SeriesInstanceUID
    sm_instance_index ||--o{ contrast_index : SeriesInstanceUID
    seg_index ||--o{ ann_index : SeriesInstanceUID
    seg_index ||--o{ ann_group_index : SeriesInstanceUID
    seg_index ||--o{ contrast_index : SeriesInstanceUID
    ann_index ||--o{ ann_group_index : SeriesInstanceUID
    ann_index ||--o{ contrast_index : SeriesInstanceUID
    ann_group_index ||--o{ contrast_index : SeriesInstanceUID
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
- **`StudyDate`** (`STRING`, NULLABLE): date of the study (de-identified) (DICOM
  attribute)
- **`StudyDescription`** (`STRING`, NULLABLE): textual description of the study
  content (DICOM attribute)
- **`BodyPartExamined`** (`STRING`, NULLABLE): body part imaged (not applicable
  for SM series) (DICOM attribute)
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
- **`source_DOI`** (`STRING`, NULLABLE): Digital Object Identifier (DOI) of the
  analysis results collection
- **`source_url`** (`STRING`, NULLABLE): URL for the location of additional
  information about the analysis results collection
- **`Subjects`** (`INTEGER`, NULLABLE): number of subjects analyzed in the
  analysis results collection
- **`Collections`** (`STRING`, NULLABLE): collections analyzed in the analysis
  results collection
- **`Modalities`** (`STRING`, NULLABLE): modalities corresponding to the
  analysis artifacts included in the analysis results collection
- **`Updated`** (`STRING`, NULLABLE): timestamp of the last update to the
  analysis results collection
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

## `ann_group_index`

This table contains detailed metadata about individual annotation groups within
Microscopy Bulk Simple Annotations (ANN) series in IDC. Each row corresponds to
a single annotation group, providing granular information about the graphic
type, number of annotations, property codes, and algorithm details. This table
can be joined with ann_index using SeriesInstanceUID for series-level context.
Note: ANN series are assumed to contain a single instance.

### Columns

- **`SeriesInstanceUID`** (`STRING`, NULLABLE):
- **`AnnotationGroupNumber`** (`INTEGER`, NULLABLE):
- **`AnnotationGroupUID`** (`STRING`, NULLABLE):
- **`AnnotationGroupLabel`** (`STRING`, NULLABLE):
- **`AnnotationGroupGenerationType`** (`STRING`, NULLABLE):
- **`NumberOfAnnotations`** (`INTEGER`, NULLABLE):
- **`GraphicType`** (`STRING`, NULLABLE):
- **`AnnotationPropertyCategory_code`** (`STRING`, NULLABLE): annotation
  property category code tuple (CodingSchemeDesignator:CodeValue) from DICOM
  AnnotationPropertyCategoryCodeSequence
- **`AnnotationPropertyCategory_CodeMeaning`** (`STRING`, NULLABLE):
  human-readable meaning of the annotation property category from DICOM
  AnnotationPropertyCategoryCodeSequence
- **`AnnotationPropertyType_code`** (`STRING`, NULLABLE): annotation property
  type code tuple (CodingSchemeDesignator:CodeValue) from DICOM
  AnnotationPropertyTypeCodeSequence
- **`AnnotationPropertyType_CodeMeaning`** (`STRING`, NULLABLE): human-readable
  meaning of the annotation property type from DICOM
  AnnotationPropertyTypeCodeSequence
- **`AlgorithmName`** (`STRING`, NULLABLE): name of the algorithm from DICOM
  AlgorithmName attribute in AnnotationGroupAlgorithmIdentificationSequence
  (when AnnotationGroupGenerationType is AUTOMATIC)

## `ann_index`

This table contains metadata about the Microscopy Bulk Simple Annotations (ANN)
series available in IDC. Each row corresponds to a DICOM series containing
annotations, and includes attributes such as the annotation coordinate type and
references to the annotated image series. For detailed group-level information
(counts, graphic types, property codes), join with ann_group_index using
SeriesInstanceUID. This table can be joined with the main idc_index table using
the SeriesInstanceUID column. Note: ANN series are assumed to contain a single
instance.

### Columns

- **`SeriesInstanceUID`** (`STRING`, NULLABLE):
- **`AnnotationCoordinateType`** (`STRING`, NULLABLE):
- **`referenced_SeriesInstanceUID`** (`STRING`, NULLABLE): SeriesInstanceUID of
  the referenced image series that the annotations apply to

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
- **`Updated`** (`STRING`, NULLABLE): timestamp of the last update to the
  collection
- **`Description`** (`STRING`, NULLABLE): detailed information about the
  collection

## `contrast_index`

This table contains one row per DICOM series that has contrast agent
information. It captures contrast bolus metadata from CT, MR, PT, XA, and RF
imaging modalities, including the agent name, ingredient, and administration
route. Only series with at least one non-null contrast attribute are included.
This table can be joined with the main idc_index table using the
SeriesInstanceUID column.

### Columns

- **`SeriesInstanceUID`** (`STRING`, NULLABLE): DICOM SeriesInstanceUID
  identifier of the imaging series
- **`ContrastBolusAgent`** (`STRING`, REPEATED): distinct contrast agent names
  used in the series as defined in DICOM ContrastBolusAgent attribute
- **`ContrastBolusIngredient`** (`STRING`, REPEATED): distinct contrast agent
  ingredients used in the series as defined in DICOM ContrastBolusIngredient
  attribute
- **`ContrastBolusRoute`** (`STRING`, REPEATED): distinct contrast
  administration routes used in the series as defined in DICOM
  ContrastBolusRoute attribute

## `seg_index`

This table contains one row per DICOM Segmentation SeriesInstanceUID available
from IDC, and captures key metadata about the segmentation series including the
number of segments, segmentation type, algorithm type and name, and the
segmented image series.

### Columns

- **`SeriesInstanceUID`** (`STRING`, NULLABLE): DICOM SeriesInstanceUID
  identifier of the segmentation series
- **`SegmentationType`** (`STRING`, NULLABLE): Type of segmentation as defined
  in DICOM SegmentationType attribute
- **`total_segments`** (`INTEGER`, NULLABLE): Number of segments in the
  segmentation series obtained by counting distinct DICOM SegmentNumber values
  in the DICOM SegmentatationSequence
- **`AlgorithmType`** (`STRING`, NULLABLE): Segmentation algorithm type as
  available in DICOM SegmentAlgorithmType
- **`AlgorithmName`** (`STRING`, NULLABLE): Segmentation algorithm name as
  available in DICOM SegmentAlgorithmName
- **`segmented_SeriesInstanceUID`** (`STRING`, NULLABLE): SeriesInstanceUID of
  the referenced image series that the segmentation applies to

## `sm_index`

This table contains metadata about the slide microscopy (SM) series available in
IDC. Each row corresponds to a DICOM series, and contains attributes specific to
SM series, such as the pixel spacing at the maximum resolution layer, the power
of the objective lens used to digitize the slide, and the anatomic location from
where the imaged specimen was collected. This table can be joined with the main
index table using the `SeriesInstanceUID` column.

### Columns

- **`SeriesInstanceUID`** (`STRING`, NULLABLE):
- **`embeddingMedium_CodeMeaning`** (`STRING`, REPEATED): embedding medium
  CodeMeaning from DICOM SpecimenPreparationSequence in
  SpecimenDescriptionSequence
- **`embeddingMedium_code_designator_value_str`** (`STRING`, REPEATED):
  embedding medium code tuple from DICOM SpecimenPreparationSequence in
  SpecimenDescriptionSequence
- **`tissueFixative_CodeMeaning`** (`STRING`, REPEATED): tissue fixative
  CodeMeaning from DICOM SpecimenPreparationSequence in
  SpecimenDescriptionSequence
- **`tissueFixative_code_designator_value_str`** (`STRING`, REPEATED): tissue
  fixative code tuple from DICOM SpecimenPreparationSequence in
  SpecimenDescriptionSequence
- **`staining_usingSubstance_CodeMeaning`** (`STRING`, REPEATED): staining
  substances CodeMeaning from DICOM SpecimenPreparationSequence in
  SpecimenDescriptionSequence
- **`staining_usingSubstance_code_designator_value_str`** (`STRING`, REPEATED):
  staining substances code tuple from DICOM SpecimenPreparationSequence in
  SpecimenDescriptionSequence
- **`min_PixelSpacing_2sf`** (`FLOAT`, NULLABLE): pixel spacing in mm at the
  maximum resolution layer, rounded to 2 significant figures, derived from DICOM
  PixelSpacing attribute
- **`max_TotalPixelMatrixColumns`** (`INTEGER`, NULLABLE): width of the image at
  the maximum resolution from DICOM TotalPixelMatrixColumns attribute
- **`max_TotalPixelMatrixRows`** (`INTEGER`, NULLABLE): height of the image at
  the maximum resolution from DICOM TotalPixelMatrixRows attribute
- **`ObjectiveLensPower`** (`INTEGER`, NULLABLE): power of the objective lens
  from DICOM ObjectiveLensPower attribute in OpticalPathSequence
- **`primaryAnatomicStructure_code_designator_value_str`** (`STRING`, NULLABLE):
  anatomic location code tuple from DICOM PrimaryAnatomicStructureSequence in
  SpecimenDescriptionSequence
- **`primaryAnatomicStructure_CodeMeaning`** (`STRING`, NULLABLE): anatomic
  location CodeMeaning from DICOM PrimaryAnatomicStructureSequence in
  SpecimenDescriptionSequence
- **`primaryAnatomicStructureModifier_code_designator_value_str`** (`STRING`,
  NULLABLE): specimen modifier code tuple from DICOM
  PrimaryAnatomicStructureModifierSequence (when available)
- **`primaryAnatomicStructureModifier_CodeMeaning`** (`STRING`, NULLABLE):
  specimen modifier CodeMeaning from DICOM
  PrimaryAnatomicStructureModifierSequence (when available)
- **`illuminationType_code_designator_value_str`** (`STRING`, NULLABLE):
  illumination type code tuple from DICOM IlluminationTypeCodeSequence in
  OpticalPathSequence
- **`illuminationType_CodeMeaning`** (`STRING`, NULLABLE): illumination type
  CodeMeaning from DICOM IlluminationTypeCodeSequence in OpticalPathSequence
- **`admittingDiagnosis_code_designator_value_str`** (`STRING`, NULLABLE):
  admitting diagnosis code tuple from DICOM AdmittingDiagnosesCodeSequence (when
  available)
- **`admittingDiagnosis_CodeMeaning`** (`STRING`, NULLABLE): admitting diagnosis
  CodeMeaning from DICOM AdmittingDiagnosesCodeSequence (when available)

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
