# Metadata attributes in `idc-index`'s index tables

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
  - `illuminationType`: specifies the type of illumination used when obtaining
    the image

In case of `embeddingMedium`, `tissueFixative`, `staining_usingSubstance`,
`primaryAnatomicStructure`, `primaryAnatomicStructureModifier` and
`illuminationType` the attributes exist with suffix `_code_designator_value_str`
and `_CodeMeaning`, which indicates whether the column contains
CodeSchemeDesignator and CodeValue, or CodeMeaning. If this is new to you, a
brief explanation on the three-value based coding scheme in DICOM can be found
at https://learn.canceridc.dev/dicom/coding-schemes.

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
