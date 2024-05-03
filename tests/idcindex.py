from __future__ import annotations

import logging
import os
import tempfile
import unittest
from itertools import product

import pytest
from idc_index import index

# Run tests using the following command from the root of the repository:
# python -m unittest -vv tests/idcindex.py

logging.basicConfig(level=logging.INFO)


@pytest.fixture(autouse=True)
def _change_test_dir(request, monkeypatch):
    monkeypatch.chdir(request.fspath.dirname)


class TestIDCClient(unittest.TestCase):
    def setUp(self):
        self.client = index.IDCClient()

        logger = logging.getLogger("idc_index")
        logger.setLevel(logging.DEBUG)

    def test_get_collections(self):
        collections = self.client.get_collections()
        self.assertIsNotNone(collections)

    def test_get_idc_version(self):
        idc_version = self.client.get_idc_version()
        self.assertIsNotNone(idc_version)
        self.assertTrue(idc_version.startswith("v"))

    def test_get_patients(self):
        patients = self.client.get_patients(
            collection_id="tcga_gbm", outputFormat="list"
        )

        patients = self.client.get_patients(
            collection_id=["qin_prostate_repeatability", "phantom_fda"],
            outputFormat="list",
        )

        self.assertIsNotNone(patients)

    def test_get_studies(self):
        studies = self.client.get_dicom_studies(
            patientId="PCAMPMRI-00001", outputFormat="list"
        )

        self.assertIsNotNone(studies)

        studies = self.client.get_dicom_studies(
            patientId=["PCAMPMRI-00001", "NoduleLayout_1"], outputFormat="list"
        )

        self.assertIsNotNone(studies)

    def test_get_series(self):
        """
        Query used for selecting the smallest series/studies:

        SELECT
            StudyInstanceUID,
            ARRAY_AGG(DISTINCT(collection_id)) AS collection,
            ARRAY_AGG(DISTINCT(series_aws_url)) AS aws_url,
            ARRAY_AGG(DISTINCT(series_gcs_url)) AS gcs_url,
            COUNT(DISTINCT(SOPInstanceUID)) AS num_instances,
            SUM(instance_size) AS series_size
        FROM
            `bigquery-public-data.idc_current.dicom_all`
        GROUP BY
            StudyInstanceUID
        HAVING
            num_instances > 2
        ORDER BY
            series_size asc
        LIMIT
            10
        """
        series = self.client.get_dicom_series(
            studyInstanceUID="1.3.6.1.4.1.14519.5.2.1.6279.6001.175012972118199124641098335511",
            outputFormat="list",
        )

        self.assertIsNotNone(series)

        series = self.client.get_dicom_series(
            studyInstanceUID=[
                "1.3.6.1.4.1.14519.5.2.1.1239.1759.691327824408089993476361149761",
                "1.3.6.1.4.1.14519.5.2.1.1239.1759.272272273744698671736205545239",
            ],
            outputFormat="list",
        )

        self.assertIsNotNone(series)

    def test_download_dicom_series(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.client.download_dicom_series(
                seriesInstanceUID="1.3.6.1.4.1.14519.5.2.1.7695.1700.153974929648969296590126728101",
                downloadDir=temp_dir,
            )
            self.assertNotEqual(len(os.listdir(temp_dir)), 0)

    def test_download_from_selection(self):
        # Define the values for each optional parameter
        dry_run_values = [True, False]
        quiet_values = [True, False]
        show_progress_bar_values = [True, False]
        use_s5cmd_sync_values = [True, False]
        dirTemplateValues = [
            None,
            "%collection_id_%PatientID/%Modality-%StudyInstanceUID%SeriesInstanceUID",
            "%collection_id%PatientID-%Modality_%StudyInstanceUID/%SeriesInstanceUID",
            "%collection_id-%PatientID_%Modality/%StudyInstanceUID-%SeriesInstanceUID",
            "%collection_id_%PatientID/%Modality/%StudyInstanceUID_%SeriesInstanceUID",
        ]

        # Generate all combinations of optional parameters
        combinations = product(
            dry_run_values,
            quiet_values,
            show_progress_bar_values,
            use_s5cmd_sync_values,
            dirTemplateValues,
        )

        # Test each combination
        for (
            dry_run,
            quiet,
            show_progress_bar,
            use_s5cmd_sync,
            dirTemplate,
        ) in combinations:
            with tempfile.TemporaryDirectory() as temp_dir:
                self.client.download_from_selection(
                    downloadDir=temp_dir,
                    dry_run=dry_run,
                    patientId=None,
                    studyInstanceUID="1.3.6.1.4.1.14519.5.2.1.7695.1700.114861588187429958687900856462",
                    seriesInstanceUID=None,
                    quiet=quiet,
                    show_progress_bar=show_progress_bar,
                    use_s5cmd_sync=use_s5cmd_sync,
                    dirTemplate=dirTemplate,
                )

                if not dry_run:
                    self.assertNotEqual(len(os.listdir(temp_dir)), 0)

    def test_sql_queries(self):
        df = self.client.sql_query("SELECT DISTINCT(collection_id) FROM index")

        self.assertIsNotNone(df)

    def test_download_from_aws_manifest(self):
        # Define the values for each optional parameter
        quiet_values = [True, False]
        validate_manifest_values = [True, False]
        show_progress_bar_values = [True, False]
        use_s5cmd_sync_values = [True, False]
        dirTemplateValues = [
            None,
            "%collection_id/%PatientID/%Modality/%StudyInstanceUID/%SeriesInstanceUID",
            "%collection_id%PatientID%Modality%StudyInstanceUID%SeriesInstanceUID",
        ]
        # Generate all combinations of optional parameters
        combinations = product(
            quiet_values,
            validate_manifest_values,
            show_progress_bar_values,
            use_s5cmd_sync_values,
            dirTemplateValues,
        )
        # Test each combination
        for (
            quiet,
            validate_manifest,
            show_progress_bar,
            use_s5cmd_sync,
            dirTemplate,
        ) in combinations:
            with tempfile.TemporaryDirectory() as temp_dir:
                self.client.download_from_manifest(
                    manifestFile="./study_manifest_aws.s5cmd",
                    downloadDir=temp_dir,
                    quiet=quiet,
                    validate_manifest=validate_manifest,
                    show_progress_bar=show_progress_bar,
                    use_s5cmd_sync=use_s5cmd_sync,
                    dirTemplate=dirTemplate,
                )

                self.assertEqual(
                    sum([len(files) for r, d, files in os.walk(temp_dir)]), 9
                )

    def test_download_from_gcp_manifest(self):
        # Define the values for each optional parameter
        quiet_values = [True, False]
        validate_manifest_values = [True, False]
        show_progress_bar_values = [True, False]
        use_s5cmd_sync_values = [True, False]
        dirTemplateValues = [
            None,
            "%collection_id/%PatientID/%Modality/%StudyInstanceUID/%SeriesInstanceUID",
            "%collection_id_%PatientID_%Modality_%StudyInstanceUID_%SeriesInstanceUID",
        ]
        # Generate all combinations of optional parameters
        combinations = product(
            quiet_values,
            validate_manifest_values,
            show_progress_bar_values,
            use_s5cmd_sync_values,
            dirTemplateValues,
        )

        # Test each combination
        for (
            quiet,
            validate_manifest,
            show_progress_bar,
            use_s5cmd_sync,
            dirTemplate,
        ) in combinations:
            with tempfile.TemporaryDirectory() as temp_dir:
                self.client.download_from_manifest(
                    manifestFile="./study_manifest_gcs.s5cmd",
                    downloadDir=temp_dir,
                    quiet=quiet,
                    validate_manifest=validate_manifest,
                    show_progress_bar=show_progress_bar,
                    use_s5cmd_sync=use_s5cmd_sync,
                    dirTemplate=dirTemplate,
                )

                self.assertEqual(
                    sum([len(files) for r, d, files in os.walk(temp_dir)]), 9
                )

    def test_download_from_bogus_manifest(self):
        # Define the values for each optional parameter
        quiet_values = [True, False]
        validate_manifest_values = [True, False]
        show_progress_bar_values = [True, False]
        use_s5cmd_sync_values = [True, False]

        # Generate all combinations of optional parameters
        combinations = product(
            quiet_values,
            validate_manifest_values,
            show_progress_bar_values,
            use_s5cmd_sync_values,
        )

        # Test each combination
        for (
            quiet,
            validate_manifest,
            show_progress_bar,
            use_s5cmd_sync,
        ) in combinations:
            with tempfile.TemporaryDirectory() as temp_dir:
                self.client.download_from_manifest(
                    manifestFile="./study_manifest_bogus.s5cmd",
                    downloadDir=temp_dir,
                    quiet=quiet,
                    validate_manifest=validate_manifest,
                    show_progress_bar=show_progress_bar,
                    use_s5cmd_sync=use_s5cmd_sync,
                )

                self.assertEqual(len(os.listdir(temp_dir)), 0)


if __name__ == "__main__":
    unittest.main()
