# Index Tables Reference

This page provides a comprehensive reference for all index tables available in
`idc-index`. The documentation is automatically generated from the schemas
provided by `idc-index-data` (version 24.2.0).

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
    ct_index {
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
    mr_index {
        STRING SeriesInstanceUID
    }
    prior_versions_index {
        STRING PatientID
        STRING SeriesInstanceUID
        STRING StudyInstanceUID
        STRING collection_id
        STRING crdc_series_uuid
    }
    pt_index {
        STRING SeriesInstanceUID
    }
    rtstruct_index {
        STRING SeriesInstanceUID
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
    volume_geometry_index {
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
    index ||--o{ volume_geometry_index : SeriesInstanceUID
    index ||--o{ rtstruct_index : SeriesInstanceUID
    index ||--o{ ct_index : SeriesInstanceUID
    index ||--o{ mr_index : SeriesInstanceUID
    index ||--o{ pt_index : SeriesInstanceUID
    prior_versions_index ||--o{ collections_index : collection_id
    prior_versions_index ||--o{ clinical_index : collection_id
    prior_versions_index ||--o{ sm_index : SeriesInstanceUID
    prior_versions_index ||--o{ sm_instance_index : SeriesInstanceUID
    prior_versions_index ||--o{ seg_index : SeriesInstanceUID
    prior_versions_index ||--o{ ann_index : SeriesInstanceUID
    prior_versions_index ||--o{ ann_group_index : SeriesInstanceUID
    prior_versions_index ||--o{ contrast_index : SeriesInstanceUID
    prior_versions_index ||--o{ volume_geometry_index : SeriesInstanceUID
    prior_versions_index ||--o{ rtstruct_index : SeriesInstanceUID
    prior_versions_index ||--o{ ct_index : SeriesInstanceUID
    prior_versions_index ||--o{ mr_index : SeriesInstanceUID
    prior_versions_index ||--o{ pt_index : SeriesInstanceUID
    collections_index ||--o{ clinical_index : collection_id
    sm_index ||--o{ sm_instance_index : SeriesInstanceUID
    sm_index ||--o{ seg_index : SeriesInstanceUID
    sm_index ||--o{ ann_index : SeriesInstanceUID
    sm_index ||--o{ ann_group_index : SeriesInstanceUID
    sm_index ||--o{ contrast_index : SeriesInstanceUID
    sm_index ||--o{ volume_geometry_index : SeriesInstanceUID
    sm_index ||--o{ rtstruct_index : SeriesInstanceUID
    sm_index ||--o{ ct_index : SeriesInstanceUID
    sm_index ||--o{ mr_index : SeriesInstanceUID
    sm_index ||--o{ pt_index : SeriesInstanceUID
    sm_instance_index ||--o{ seg_index : SeriesInstanceUID
    sm_instance_index ||--o{ ann_index : SeriesInstanceUID
    sm_instance_index ||--o{ ann_group_index : SeriesInstanceUID
    sm_instance_index ||--o{ contrast_index : SeriesInstanceUID
    sm_instance_index ||--o{ volume_geometry_index : SeriesInstanceUID
    sm_instance_index ||--o{ rtstruct_index : SeriesInstanceUID
    sm_instance_index ||--o{ ct_index : SeriesInstanceUID
    sm_instance_index ||--o{ mr_index : SeriesInstanceUID
    sm_instance_index ||--o{ pt_index : SeriesInstanceUID
    seg_index ||--o{ ann_index : SeriesInstanceUID
    seg_index ||--o{ ann_group_index : SeriesInstanceUID
    seg_index ||--o{ contrast_index : SeriesInstanceUID
    seg_index ||--o{ volume_geometry_index : SeriesInstanceUID
    seg_index ||--o{ rtstruct_index : SeriesInstanceUID
    seg_index ||--o{ ct_index : SeriesInstanceUID
    seg_index ||--o{ mr_index : SeriesInstanceUID
    seg_index ||--o{ pt_index : SeriesInstanceUID
    ann_index ||--o{ ann_group_index : SeriesInstanceUID
    ann_index ||--o{ contrast_index : SeriesInstanceUID
    ann_index ||--o{ volume_geometry_index : SeriesInstanceUID
    ann_index ||--o{ rtstruct_index : SeriesInstanceUID
    ann_index ||--o{ ct_index : SeriesInstanceUID
    ann_index ||--o{ mr_index : SeriesInstanceUID
    ann_index ||--o{ pt_index : SeriesInstanceUID
    ann_group_index ||--o{ contrast_index : SeriesInstanceUID
    ann_group_index ||--o{ volume_geometry_index : SeriesInstanceUID
    ann_group_index ||--o{ rtstruct_index : SeriesInstanceUID
    ann_group_index ||--o{ ct_index : SeriesInstanceUID
    ann_group_index ||--o{ mr_index : SeriesInstanceUID
    ann_group_index ||--o{ pt_index : SeriesInstanceUID
    contrast_index ||--o{ volume_geometry_index : SeriesInstanceUID
    contrast_index ||--o{ rtstruct_index : SeriesInstanceUID
    contrast_index ||--o{ ct_index : SeriesInstanceUID
    contrast_index ||--o{ mr_index : SeriesInstanceUID
    contrast_index ||--o{ pt_index : SeriesInstanceUID
    volume_geometry_index ||--o{ rtstruct_index : SeriesInstanceUID
    volume_geometry_index ||--o{ ct_index : SeriesInstanceUID
    volume_geometry_index ||--o{ mr_index : SeriesInstanceUID
    volume_geometry_index ||--o{ pt_index : SeriesInstanceUID
    rtstruct_index ||--o{ ct_index : SeriesInstanceUID
    rtstruct_index ||--o{ mr_index : SeriesInstanceUID
    rtstruct_index ||--o{ pt_index : SeriesInstanceUID
    ct_index ||--o{ mr_index : SeriesInstanceUID
    ct_index ||--o{ pt_index : SeriesInstanceUID
    mr_index ||--o{ pt_index : SeriesInstanceUID
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
- **`SeriesInstanceUID`** (`STRING`, NULLABLE):
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
- **`SOPClassUID`** (`STRING`, NULLABLE): SOP Class UID identifying the type of
  DICOM object (e.g., CT Image Storage, Segmentation Storage); more specific
  than Modality for distinguishing object types (DICOM attribute)
- **`sop_class_name`** (`STRING`, NULLABLE): human-readable name of the SOP
  Class (e.g., "CT Image Storage", "Segmentation Storage"); derived from
  SOPClassUID
- **`TransferSyntaxUID`** (`STRING`, NULLABLE): Transfer Syntax UID identifying
  the encoding of the stored instances (e.g., Explicit VR Little Endian, JPEG
  2000, HTJ2K); comma-separated when a series contains instances with different
  encodings, which is common for SM (DICOM attribute)
- **`transfer_syntax_name`** (`STRING`, NULLABLE): human-readable name of the
  Transfer Syntax (e.g., "JPEG 2000", "Explicit VR Little Endian");
  comma-separated when a series contains instances with different encodings;
  derived from TransferSyntaxUID
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
- **`series_init_idc_version`** (`INTEGER`, NULLABLE): IDC data release version
  number when this series first appeared in IDC (integer, e.g., 1 for v1)
- **`series_revised_idc_version`** (`INTEGER`, NULLABLE): IDC data release
  version number when this series was most recently revised in IDC (integer,
  e.g., 24 for v24)
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
- **`subjects`** (`INTEGER`, NULLABLE): number of subjects analyzed in the
  analysis results collection
- **`collections`** (`STRING`, NULLABLE): collections analyzed in the analysis
  results collection
- **`modalities`** (`STRING`, NULLABLE): modalities corresponding to the
  analysis artifacts included in the analysis results collection
- **`updated`** (`STRING`, NULLABLE): timestamp of the last update to the
  analysis results collection
- **`license_url`** (`STRING`, NULLABLE): license URL for the analysis results
  collection
- **`license_long_name`** (`STRING`, NULLABLE): license name for the analysis
  results collection
- **`license_short_name`** (`STRING`, NULLABLE): short name for the license of
  the analysis results collection
- **`description`** (`STRING`, NULLABLE): detailed description of the analysis
  results collection
- **`citation`** (`STRING`, NULLABLE): citation for the analysis results
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
- **`cancer_types`** (`STRING`, NULLABLE): types of cancer represented in the
  collection
- **`tumor_locations`** (`STRING`, NULLABLE): locations of tumors represented in
  the collection
- **`subjects`** (`INTEGER`, NULLABLE): number of subjects in the collection
- **`species`** (`STRING`, NULLABLE): species represented in the collection
- **`sources`** (`RECORD`, REPEATED): sources of data for the collection
- **`supporting_data`** (`STRING`, NULLABLE): additional data supporting the
  collection available in IDC
- **`program_id`** (`STRING`, NULLABLE): broader initiative/category under which
  this collection is being shared
- **`status`** (`STRING`, NULLABLE): status of the collection (Completed or
  Ongoing)
- **`updated`** (`STRING`, NULLABLE): date of the last update to the collection
- **`description`** (`STRING`, NULLABLE): detailed information about the
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

## `ct_index`

This table contains one row per CT Image Storage (SOPClassUID
1.2.840.10008.5.1.4.1.1.2) DICOM series in IDC, capturing acquisition and
reconstruction parameters that are not included in the main idc_index table. The
index can be joined to idc_index on SeriesInstanceUID to combine universal
series metadata with CT-specific acquisition parameters. For XRayTubeCurrent,
Exposure, and ExposureTime — which vary across instances within a series due to
dose modulation — both min and max values are reported. All other attributes are
aggregated with ANY_VALUE (one representative instance).

### Columns

- **`SeriesInstanceUID`** (`STRING`, NULLABLE): DICOM SeriesInstanceUID — unique
  identifier of the CT series; use to join with idc_index
- **`ImageType`** (`STRING`, REPEATED): image type values as defined in DICOM
  ImageType attribute (e.g., ORIGINAL/DERIVED, PRIMARY/SECONDARY,
  AXIAL/LOCALIZER); aggregated with ANY_VALUE — constant across instances within
  a series
- **`PixelSpacing_row_mm`** (`FLOAT`, NULLABLE): in-plane pixel spacing along
  the row direction in mm, derived from DICOM PixelSpacing[0]; a subset of CT
  series have anisotropic spacing where this differs from PixelSpacing_col_mm;
  aggregated with ANY_VALUE — constant across instances within a series
- **`PixelSpacing_col_mm`** (`FLOAT`, NULLABLE): in-plane pixel spacing along
  the column direction in mm, derived from DICOM PixelSpacing[1]; a subset of CT
  series have anisotropic spacing where this differs from PixelSpacing_row_mm;
  aggregated with ANY_VALUE — constant across instances within a series
- **`Rows`** (`INTEGER`, NULLABLE):
- **`Columns`** (`INTEGER`, NULLABLE):
- **`SliceThickness`** (`FLOAT`, NULLABLE): nominal reconstructed slice
  thickness in mm as defined in DICOM SliceThickness attribute; aggregated with
  ANY_VALUE — constant across instances within a series
- **`KVP`** (`FLOAT`, NULLABLE): peak kilovoltage of the X-ray tube in kV as
  defined in DICOM KVP attribute; constant across instances — aggregated with
  ANY_VALUE
- **`ScanOptions`** (`STRING`, REPEATED): acquisition scan options as defined in
  DICOM ScanOptions attribute (e.g., HELICAL MODE, AXIAL MODE, SCOUT MODE); may
  contain multiple values; aggregated with ANY_VALUE — constant across instances
  within a series
- **`ConvolutionKernel`** (`STRING`, REPEATED): reconstruction convolution
  kernel as defined in DICOM ConvolutionKernel attribute; vendor-specific string
  (e.g., B30f, STANDARD, LUNG); may contain multiple values; aggregated with
  ANY_VALUE — constant across instances within a series
- **`GantryDetectorTilt`** (`FLOAT`, NULLABLE): nominal angle of the scanning
  gantry in degrees as defined in DICOM GantryDetectorTilt attribute; non-zero
  for gantry-tilted acquisitions; constant across instances — aggregated with
  ANY_VALUE
- **`XRayTubeCurrent_min`** (`FLOAT`, NULLABLE): minimum X-ray tube current in
  mA across all instances in the series, derived from DICOM XRayTubeCurrent
  attribute; equals XRayTubeCurrent_max for fixed-current acquisitions; lower
  than XRayTubeCurrent_max for dose-modulated acquisitions (MIN across all
  instances)
- **`XRayTubeCurrent_max`** (`FLOAT`, NULLABLE): maximum X-ray tube current in
  mA across all instances in the series, derived from DICOM XRayTubeCurrent
  attribute; equals XRayTubeCurrent_min for fixed-current acquisitions; higher
  than XRayTubeCurrent_min for dose-modulated acquisitions (MAX across all
  instances)
- **`FilterType`** (`STRING`, NULLABLE): type of filter used in the acquisition
  as defined in DICOM FilterType attribute (e.g., WEDGE, BUTTERFLY, FLAT);
  constant across instances — aggregated with ANY_VALUE
- **`Exposure_min`** (`FLOAT`, NULLABLE): minimum exposure in mAs across all
  instances in the series, derived from DICOM Exposure attribute; equals
  Exposure_max for fixed-exposure acquisitions; lower than Exposure_max for
  dose-modulated acquisitions (MIN across all instances)
- **`Exposure_max`** (`FLOAT`, NULLABLE): maximum exposure in mAs across all
  instances in the series, derived from DICOM Exposure attribute; equals
  Exposure_min for fixed-exposure acquisitions; higher than Exposure_min for
  dose-modulated acquisitions (MAX across all instances)
- **`ExposureTime_min`** (`FLOAT`, NULLABLE): minimum duration of the X-ray
  exposure in ms across all instances in the series, derived from DICOM
  ExposureTime attribute (MIN across all instances)
- **`ExposureTime_max`** (`FLOAT`, NULLABLE): maximum duration of the X-ray
  exposure in ms across all instances in the series, derived from DICOM
  ExposureTime attribute (MAX across all instances)
- **`DataCollectionDiameter`** (`FLOAT`, NULLABLE): diameter of the region over
  which data were collected in mm as defined in DICOM DataCollectionDiameter
  attribute; constant across instances — aggregated with ANY_VALUE
- **`ReconstructionDiameter`** (`FLOAT`, NULLABLE): diameter of the
  reconstruction field of view in mm as defined in DICOM ReconstructionDiameter
  attribute; aggregated with ANY_VALUE — constant across instances within a
  series
- **`SpiralPitchFactor`** (`FLOAT`, NULLABLE): ratio of the beam pitch for
  helical CT as defined in DICOM SpiralPitchFactor attribute; NULL for
  non-helical (sequential/axial) acquisitions; constant across instances —
  aggregated with ANY_VALUE

## `mr_index`

This table contains one row per MR Image Storage (SOPClassUID
1.2.840.10008.5.1.4.1.1.4) DICOM series in IDC, capturing MR acquisition and
sequence parameters that are not included in the main idc_index table. The index
can be joined to idc_index on SeriesInstanceUID to combine universal series
metadata with MR-specific acquisition parameters. EchoTime and DiffusionBValue
are reported as arrays of all distinct per-instance values because they
legitimately differ across instances within multi-echo and diffusion-weighted
series respectively. All other attributes are aggregated with ANY_VALUE (one
representative instance).

### Columns

- **`SeriesInstanceUID`** (`STRING`, NULLABLE): DICOM SeriesInstanceUID — unique
  identifier of the MR series; use to join with idc_index
- **`MagneticFieldStrength`** (`FLOAT`, NULLABLE): static magnetic field
  strength in Tesla as defined in DICOM MagneticFieldStrength attribute;
  constant across instances within a series — aggregated with ANY_VALUE
- **`ScanningSequence`** (`STRING`, REPEATED): pulse sequence type as defined in
  DICOM ScanningSequence attribute (SE = Spin Echo, GR = Gradient Recalled, IR =
  Inversion Recovery, EP = Echo Planar); may contain multiple values; constant
  across instances — aggregated with ANY_VALUE
- **`SequenceVariant`** (`STRING`, REPEATED): variant of the scanning sequence
  as defined in DICOM SequenceVariant attribute (SK = Segmented k-Space, MTC =
  Magnetization Transfer Contrast, SS = Steady State, TRSS = Time Reversed
  Steady State, SP = Spoiled, MP = MAG Prepared, OSP = Oversampling Phase, NONE
  = No sequence variant); may contain multiple values; constant across instances
  — aggregated with ANY_VALUE
- **`MRAcquisitionType`** (`STRING`, NULLABLE): whether the acquisition is 2D or
  3D as defined in DICOM MRAcquisitionType attribute; constant across instances
  — aggregated with ANY_VALUE
- **`EchoTime`** (`FLOAT`, REPEATED): distinct echo times in ms present in the
  series, derived from DICOM EchoTime attribute; aggregated as
  ARRAY_AGG(DISTINCT) across all instances because EchoTime legitimately varies
  in multi-echo sequences; single-element array for single-echo series,
  multi-element array for multi-echo series (e.g., [2.46, 4.92, 7.38])
- **`RepetitionTime`** (`FLOAT`, NULLABLE): repetition time in ms as defined in
  DICOM RepetitionTime attribute; aggregated with ANY_VALUE — constant across
  instances within a series
- **`EchoTrainLength`** (`INTEGER`, NULLABLE): number of echoes in the echo
  train as defined in DICOM EchoTrainLength attribute; constant across instances
  — aggregated with ANY_VALUE
- **`FlipAngle`** (`FLOAT`, NULLABLE): flip angle in degrees as defined in DICOM
  FlipAngle attribute; aggregated with ANY_VALUE — constant across instances
  within a series
- **`PixelBandwidth`** (`FLOAT`, NULLABLE): receiver bandwidth per pixel in Hz
  as defined in DICOM PixelBandwidth attribute; aggregated with ANY_VALUE —
  constant across instances within a series
- **`ImagingFrequency`** (`FLOAT`, NULLABLE): Larmor resonance frequency in MHz
  as defined in DICOM ImagingFrequency attribute; proportional to
  MagneticFieldStrength (42.577 MHz/T for proton); constant across instances —
  aggregated with ANY_VALUE
- **`ImagedNucleus`** (`STRING`, NULLABLE): nucleus used for imaging as defined
  in DICOM ImagedNucleus attribute (e.g., 1H for proton, 31P, 23Na); constant
  across instances — aggregated with ANY_VALUE
- **`PixelSpacing_row_mm`** (`FLOAT`, NULLABLE): in-plane pixel spacing along
  the row direction in mm, derived from DICOM PixelSpacing[0]; MR pixel spacing
  is isotropic in almost all series in IDC; aggregated with ANY_VALUE — constant
  across instances within a series
- **`PixelSpacing_col_mm`** (`FLOAT`, NULLABLE): in-plane pixel spacing along
  the column direction in mm, derived from DICOM PixelSpacing[1]; MR pixel
  spacing is isotropic in almost all series in IDC; aggregated with ANY_VALUE —
  constant across instances within a series
- **`Rows`** (`INTEGER`, NULLABLE):
- **`Columns`** (`INTEGER`, NULLABLE):
- **`SliceThickness`** (`FLOAT`, NULLABLE): nominal slice thickness in mm as
  defined in DICOM SliceThickness attribute; aggregated with ANY_VALUE —
  constant across instances within a series
- **`InversionTime`** (`FLOAT`, NULLABLE): inversion time in ms as defined in
  DICOM InversionTime attribute; populated only for inversion recovery
  sequences, NULL otherwise; constant across instances — aggregated with
  ANY_VALUE
- **`ReceiveCoilName`** (`STRING`, NULLABLE): name of the receiver coil used as
  defined in DICOM ReceiveCoilName attribute; aggregated with ANY_VALUE —
  constant across instances within a series
- **`SequenceName`** (`STRING`, NULLABLE): manufacturer-specific pulse sequence
  name as defined in DICOM SequenceName attribute (e.g., _tfl_ for Siemens
  FLASH, _ep_b1000_ for Siemens EPI diffusion); aggregated with ANY_VALUE —
  constant across instances within a series
- **`DiffusionBValue`** (`FLOAT`, REPEATED): distinct diffusion b-values in
  s/mm² present in the series, derived from DICOM DiffusionBValue attribute;
  aggregated as ARRAY_AGG(DISTINCT) across all instances because DiffusionBValue
  legitimately varies across instances in diffusion-weighted series; empty array
  for non-DWI series; multi-element for DWI (e.g., [0.0, 1000.0])
- **`NumberOfTemporalPositions`** (`INTEGER`, NULLABLE): number of temporal
  positions (time frames) in the series as defined in DICOM
  NumberOfTemporalPositions attribute; populated for dynamic (DCE-MRI) series;
  NULL otherwise; constant across instances — aggregated with ANY_VALUE

## `pt_index`

This table contains one row per Positron Emission Tomography Image Storage
(SOPClassUID 1.2.840.10008.5.1.4.1.1.128) DICOM series in IDC, capturing PET
acquisition, reconstruction and radiopharmaceutical parameters that are not
included in the main idc_index table. The index can be joined to idc_index on
SeriesInstanceUID to combine universal series metadata with PET-specific
acquisition parameters. ActualFrameDuration is reported as an array of all
distinct per-instance values because it legitimately varies across frames in
dynamic (multi-frame) PET acquisitions. All other attributes are constant within
a series and are aggregated with ANY_VALUE.

### Columns

- **`SeriesInstanceUID`** (`STRING`, NULLABLE): DICOM SeriesInstanceUID — unique
  identifier of the PET series; use to join with idc_index
- **`SeriesType`** (`STRING`, NULLABLE): acquisition type of the series as
  defined in DICOM SeriesType attribute, encoded as a slash-separated string of
  the two type values (e.g., STATIC/IMAGE, DYNAMIC/IMAGE, GATED/IMAGE, WHOLE
  BODY/IMAGE); constant across instances — aggregated with
  ANY_VALUE(ARRAY_TO_STRING(SeriesType, '/'))
- **`Units`** (`STRING`, NULLABLE): pixel value units as defined in DICOM Units
  attribute (e.g., BQML = Bq/mL, CNTS = counts, CPS = counts/s, GML = g/mL);
  constant across instances — aggregated with ANY_VALUE
- **`DecayCorrection`** (`STRING`, NULLABLE): type of decay correction applied
  as defined in DICOM DecayCorrection attribute (START = corrected to scan start
  time, ADMIN = corrected to radiopharmaceutical administration time, NONE = no
  correction); constant across instances — aggregated with ANY_VALUE
- **`CorrectedImage`** (`STRING`, REPEATED): list of corrections applied to the
  image as defined in DICOM CorrectedImage attribute (e.g., ATTN = attenuation,
  SCAT = scatter, DECY = decay, RAN = randoms); may contain multiple values;
  constant across instances — aggregated with ANY_VALUE
- **`RandomsCorrectionMethod`** (`STRING`, NULLABLE): method used for randoms
  correction as defined in DICOM RandomsCorrectionMethod attribute; constant
  across instances — aggregated with ANY_VALUE
- **`ReconstructionMethod`** (`STRING`, NULLABLE): reconstruction algorithm as
  defined in DICOM ReconstructionMethod attribute (e.g., OSEM, FBP); constant
  across instances — aggregated with ANY_VALUE
- **`ActualFrameDuration`** (`FLOAT`, REPEATED): distinct actual frame durations
  in ms present in the series, derived from DICOM ActualFrameDuration attribute;
  aggregated as ARRAY_AGG(DISTINCT) across all instances because
  ActualFrameDuration legitimately varies across frames in dynamic PET
  acquisitions; single-element array for static PET, multi-element for dynamic
  PET with variable frame durations
- **`ScatterCorrectionMethod`** (`STRING`, NULLABLE): scatter correction method
  as defined in DICOM ScatterCorrectionMethod attribute; constant across
  instances — aggregated with ANY_VALUE
- **`AttenuationCorrectionMethod`** (`STRING`, NULLABLE): attenuation correction
  method as defined in DICOM AttenuationCorrectionMethod attribute; constant
  across instances — aggregated with ANY_VALUE
- **`RadionuclideCodeMeaning`** (`STRING`, NULLABLE): code meaning of the
  radionuclide used, from
  RadiopharmaceuticalInformationSequence[0].RadionuclideCodeSequence[0].CodeMeaning;
  (e.g., Fluorine F18, Gallium Ga-68); constant across instances — aggregated
  with ANY_VALUE
- **`RadionuclideTotalDose`** (`FLOAT`, NULLABLE): total administered dose of
  the radionuclide in Bq, from
  RadiopharmaceuticalInformationSequence[0].RadionuclideTotalDose; constant
  across instances — aggregated with ANY_VALUE
- **`RadiopharmaceuticalStartTime`** (`STRING`, NULLABLE): time of
  radiopharmaceutical administration (injection time), from
  RadiopharmaceuticalInformationSequence[0].RadiopharmaceuticalStartTime; stored
  as STRING (HH:MM:SS.FFFFFF) because DICOM TIME type is not supported in
  parquet output; constant across instances — aggregated with ANY_VALUE
- **`Radiopharmaceutical`** (`STRING`, NULLABLE): free-text name of the
  radiopharmaceutical as defined in
  RadiopharmaceuticalInformationSequence[0].Radiopharmaceutical (e.g.,
  Fluorodeoxyglucose F^18^); values are not standardized across sites; see
  RadionuclideCodeMeaning for a more consistent alternative; constant across
  instances — aggregated with ANY_VALUE
- **`PixelSpacing_row_mm`** (`FLOAT`, NULLABLE): in-plane pixel spacing along
  the row direction in mm, derived from DICOM PixelSpacing[0]; PET pixel spacing
  is isotropic in almost all series in IDC; aggregated with ANY_VALUE — constant
  across instances within a series
- **`PixelSpacing_col_mm`** (`FLOAT`, NULLABLE): in-plane pixel spacing along
  the column direction in mm, derived from DICOM PixelSpacing[1]; PET pixel
  spacing is isotropic in almost all series in IDC; aggregated with ANY_VALUE —
  constant across instances within a series
- **`Rows`** (`INTEGER`, NULLABLE):
- **`Columns`** (`INTEGER`, NULLABLE):
- **`SliceThickness`** (`FLOAT`, NULLABLE): nominal slice thickness in mm as
  defined in DICOM SliceThickness attribute; constant across instances —
  aggregated with ANY_VALUE
- **`NumberOfSlices`** (`INTEGER`, NULLABLE): total number of slices in the
  series as defined in DICOM NumberOfSlices attribute; constant across instances
  — aggregated with ANY_VALUE
- **`NumberOfTimeSlices`** (`INTEGER`, NULLABLE): number of time frames in the
  series as defined in DICOM NumberOfTimeSlices attribute; populated only for
  dynamic (multi-frame) PET series, NULL for static PET; constant across
  instances — aggregated with ANY_VALUE

## `rtstruct_index`

This table contains one row per DICOM RT Structure Set (RTSTRUCT)
SeriesInstanceUID available from IDC, and captures key metadata about the
structure set including the number of ROIs, ROI names, generation algorithms,
interpreted types, and the referenced image series. Note: multi-valued columns
(ROINames, ROIGenerationAlgorithms, RTROIInterpretedTypes) are aggregated with
DISTINCT independently, so positional correspondence between columns is not
preserved.

### Columns

- **`SeriesInstanceUID`** (`STRING`, NULLABLE): DICOM SeriesInstanceUID
  identifier of the RT Structure Set series
- **`total_rois`** (`INTEGER`, NULLABLE): Number of ROIs in the structure set
  obtained by counting distinct DICOM ROINumber values in the
  StructureSetROISequence
- **`ROINames`** (`STRING`, REPEATED): Array of distinct ROI names from DICOM
  ROIName attribute in StructureSetROISequence, e.g., ["GTV", "Heart", "Liver",
  "PTV"]
- **`ROIGenerationAlgorithms`** (`STRING`, REPEATED): Array of distinct ROI
  generation algorithms from DICOM ROIGenerationAlgorithm attribute in
  StructureSetROISequence, e.g., ["AUTOMATIC", "MANUAL", "SEMIAUTOMATIC"]
- **`RTROIInterpretedTypes`** (`STRING`, REPEATED): Array of distinct ROI
  interpreted types from DICOM RTROIInterpretedType attribute in
  RTROIObservationsSequence, e.g., ["GTV", "ORGAN", "PTV"]
- **`referenced_SeriesInstanceUID`** (`STRING`, NULLABLE): SeriesInstanceUID of
  the referenced image series that the structure set applies to, extracted from
  DICOM ReferencedFrameOfReferenceSequence > RTReferencedStudySequence >
  RTReferencedSeriesSequence

## `seg_index`

This table contains one row per DICOM Segmentation SeriesInstanceUID available
from IDC, and captures key metadata about the segmentation series including the
number of segments, segmentation type, algorithm type and name, and the
segmented image series. Note: multi-valued columns (AlgorithmType,
AlgorithmName, SegmentedPropertyCategory_CodeMeanings, etc.) are aggregated with
DISTINCT independently, so positional correspondence between columns is not
preserved. For example, the first value in AlgorithmType does not necessarily
pair with the first value in AlgorithmName.

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
- **`SegmentedPropertyCategory_CodeMeanings`** (`STRING`, REPEATED): Array of
  distinct CodeMeaning values from SegmentedPropertyCategoryCodeSequence across
  all segments in the series, representing the broad category of the segmented
  property as defined in DICOM PS3.3 C.8.20.2, e.g., ["Anatomical Structure"],
  ["Morphologically Altered Structure"]
- **`SegmentedPropertyType_CodeMeanings`** (`STRING`, REPEATED): Array of
  distinct CodeMeaning values from SegmentedPropertyTypeCodeSequence across all
  segments in the series, representing the specific type of the segmented
  property as defined in DICOM PS3.3 C.8.20.2, e.g., ["Liver", "Kidney",
  "Spleen"]
- **`AnatomicRegion_CodeMeanings`** (`STRING`, REPEATED): Array of distinct
  CodeMeaning values from AnatomicRegionSequence across all segments in the
  series, representing the anatomic location of the segmented structure as
  defined in DICOM PS3.3 C.8.20.2, e.g., ["Abdomen"], ["Thorax", "Head"]

## `sm_index`

This table contains metadata about the slide microscopy (SM) series available in
IDC. Each row corresponds to a DICOM series, and contains attributes specific to
SM series, such as the pixel spacing at the maximum resolution layer, the power
of the objective lens used to digitize the slide, and the anatomic location from
where the imaged specimen was collected. This table can be joined with the main
index table using the `SeriesInstanceUID` column.

### Columns

- **`SeriesInstanceUID`** (`STRING`, NULLABLE):
- **`ContainerIdentifier`** (`STRING`, NULLABLE): identifier of the container
  (e.g., glass slide) holding the specimen from DICOM ContainerIdentifier
  attribute
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

## `version_metadata_index`

This table contains metadata about each IDC data release version. Each row
corresponds to one IDC version and captures when that version was created. This
index can be used to correlate data in other indexes (which include idc_version
columns) with the corresponding release timestamps.

### Columns

- **`idc_version`** (`INTEGER`, NULLABLE): IDC version number identifying the
  data release
- **`version_timestamp`** (`STRING`, NULLABLE): timestamp when this IDC version
  was created

## `volume_geometry_index`

This table contains one row per DICOM series from IDC for single-frame CT, MR,
and PT SOP classes, with boolean columns characterizing the geometric properties
of each series. The checks determine whether the series forms a regularly-spaced
rectilinear 3D volume (consistent orientation, spacing, dimensions, and slice
positions). Series that do not pass all checks may still be usable with
additional processing such as resampling or acquisition geometry correction
(e.g., for variable-spacing or gantry-tilted acquisitions). Oblique-aware: uses
projection-based slice position computation, which handles gantry-tilted CT,
oblique MR, and axial PET uniformly.

### Columns

- **`SeriesInstanceUID`** (`STRING`, NULLABLE): unique identifier of the DICOM
  series
- **`single_orientation`** (`BOOLEAN`, NULLABLE): TRUE if all instances share
  the same ImageOrientationPatient (DICOM attribute)
- **`orthogonal_orientation`** (`BOOLEAN`, NULLABLE): TRUE if the cross product
  of row and column orientation vectors has unit magnitude (within
  orientationTolerance), confirming orthogonal direction cosines
- **`unique_slice_positions`** (`BOOLEAN`, NULLABLE): TRUE if every instance has
  a distinct slice position along the volume normal, i.e. no duplicate or
  overlapping slices
- **`consistent_in_plane_row`** (`BOOLEAN`, NULLABLE): TRUE if the projection of
  ImagePositionPatient onto the row direction is constant across all instances
  (within inPlaneTolerance)
- **`consistent_in_plane_col`** (`BOOLEAN`, NULLABLE): TRUE if the projection of
  ImagePositionPatient onto the column direction is constant across all
  instances (within inPlaneTolerance)
- **`consistent_pixel_spacing`** (`BOOLEAN`, NULLABLE): TRUE if all instances
  share the same PixelSpacing (DICOM attribute)
- **`consistent_image_dimensions`** (`BOOLEAN`, NULLABLE): TRUE if all instances
  share the same Rows and Columns values (DICOM attributes)
- **`uniform_slice_spacing`** (`BOOLEAN`, NULLABLE): TRUE if the spacing between
  consecutive slices is constant (within relativeSliceTolerance, a relative
  fraction of expected spacing)
- **`obliquity_degrees`** (`FLOAT`, NULLABLE): angle in degrees between the
  slice normal and the nearest cardinal axis (X, Y, or Z in patient
  coordinates); 0 means pure axial, sagittal, or coronal; values above 0
  indicate oblique acquisition or gantry tilt
- **`regularly_spaced_3d_volume`** (`BOOLEAN`, NULLABLE): TRUE if all individual
  checks pass, indicating the series forms a regularly-spaced rectilinear 3D
  volume that can be loaded directly into a 3D array without resampling
