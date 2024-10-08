from __future__ import annotations

import logging
import os
import tempfile
import unittest
from itertools import product
from pathlib import Path

import pandas as pd
import pytest
import requests
from click.testing import CliRunner
from idc_index import IDCClient, cli

# Run tests using the following command from the root of the repository:
# python -m unittest -vv tests/idcindex.py
#
# run specific tests with this:
# pytest ./tests/idcindex.py::TestIDCClient.test_download_dicom_instance

logging.basicConfig(level=logging.DEBUG)


def remote_file_exists(url):
    try:
        response = requests.head(url, allow_redirects=True)
        # Check if the status code indicates success
        return response.status_code == 200
    except requests.RequestException as e:
        # Handle any exceptions (e.g., network issues)
        print(f"An error occurred: {e}")
        return False


@pytest.fixture(autouse=True)
def _change_test_dir(request, monkeypatch):
    monkeypatch.chdir(request.fspath.dirname)


class TestIDCClient(unittest.TestCase):
    def setUp(self):
        self.client = IDCClient()
        self.download_from_manifest = cli.download_from_manifest
        self.download_from_selection = cli.download_from_selection
        self.download = cli.download

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
        # Define the values for each optional parameter
        output_format_values = ["list", "dict", "df"]
        collection_id_values = [
            "htan_ohsu",
            ["ct_phantom4radiomics", "cmb_gec"],
        ]

        # Test each combination
        for collection_id in collection_id_values:
            for output_format in output_format_values:
                patients = self.client.get_patients(
                    collection_id=collection_id, outputFormat=output_format
                )

                # Check if the output format matches the expected type
                if output_format == "list":
                    self.assertIsInstance(patients, list)
                    self.assertTrue(bool(patients))  # Check that the list is not empty
                elif output_format == "dict":
                    self.assertTrue(
                        isinstance(patients, dict)
                        or (
                            isinstance(patients, list)
                            and all(isinstance(i, dict) for i in patients)
                        )
                    )  # Check that the output is either a dictionary or a list of dictionaries
                    self.assertTrue(
                        bool(patients)
                    )  # Check that the output is not empty
                elif output_format == "df":
                    self.assertIsInstance(patients, pd.DataFrame)
                    self.assertFalse(
                        patients.empty
                    )  # Check that the DataFrame is not empty

    def test_get_studies(self):
        # Define the values for each optional parameter
        output_format_values = ["list", "dict", "df"]
        patient_id_values = ["PCAMPMRI-00001", ["PCAMPMRI-00001", "NoduleLayout_1"]]

        # Test each combination
        for patient_id in patient_id_values:
            for output_format in output_format_values:
                studies = self.client.get_dicom_studies(
                    patientId=patient_id, outputFormat=output_format
                )

                # Check if the output format matches the expected type
                if output_format == "list":
                    self.assertIsInstance(studies, list)
                    self.assertTrue(bool(studies))  # Check that the list is not empty
                elif output_format == "dict":
                    self.assertTrue(
                        isinstance(studies, dict)
                        or (
                            isinstance(studies, list)
                            and all(isinstance(i, dict) for i in studies)
                        )
                    )  # Check that the output is either a dictionary or a list of dictionaries
                    self.assertTrue(bool(studies))  # Check that the output is not empty
                elif output_format == "df":
                    self.assertIsInstance(studies, pd.DataFrame)
                    self.assertFalse(
                        studies.empty
                    )  # Check that the DataFrame is not empty

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
        # Define the values for each optional parameter
        output_format_values = ["list", "dict", "df"]
        study_instance_uid_values = [
            "1.3.6.1.4.1.14519.5.2.1.6279.6001.175012972118199124641098335511",
            [
                "1.3.6.1.4.1.14519.5.2.1.1239.1759.691327824408089993476361149761",
                "1.3.6.1.4.1.14519.5.2.1.1239.1759.272272273744698671736205545239",
            ],
        ]

        # Test each combination
        for study_instance_uid in study_instance_uid_values:
            for output_format in output_format_values:
                series = self.client.get_dicom_series(
                    studyInstanceUID=study_instance_uid, outputFormat=output_format
                )

                # Check if the output format matches the expected type
                if output_format == "list":
                    self.assertIsInstance(series, list)
                    self.assertTrue(bool(series))  # Check that the list is not empty
                elif output_format == "dict":
                    self.assertTrue(
                        isinstance(series, dict)
                        or (
                            isinstance(series, list)
                            and all(isinstance(i, dict) for i in series)
                        )
                    )  # Check that the output is either a dictionary or a list of dictionaries
                elif output_format == "df":
                    self.assertIsInstance(series, pd.DataFrame)
                    self.assertFalse(
                        series.empty
                    )  # Check that the DataFrame is not empty

    def test_download_dicom_series(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.client.download_dicom_series(
                seriesInstanceUID="1.3.6.1.4.1.14519.5.2.1.7695.1700.153974929648969296590126728101",
                downloadDir=temp_dir,
            )
            self.assertEqual(sum([len(files) for r, d, files in os.walk(temp_dir)]), 3)

    def test_download_dicom_instance(self):
        i = IDCClient()
        i.fetch_index("sm_instance_index")
        with tempfile.TemporaryDirectory() as temp_dir:
            self.client.download_dicom_instance(
                sopInstanceUID="1.3.6.1.4.1.5962.99.1.528744472.1087975700.1641206284312.14.0",
                downloadDir=temp_dir,
            )

            self.assertEqual(sum([len(files) for r, d, files in os.walk(temp_dir)]), 1)

    def test_download_with_template(self):
        dirTemplateValues = [
            None,
            "%collection_id_%PatientID/%Modality-%StudyInstanceUID%SeriesInstanceUID",
            "%collection_id%PatientID-%Modality_%StudyInstanceUID/%SeriesInstanceUID",
            "%collection_id-%PatientID_%Modality/%StudyInstanceUID-%SeriesInstanceUID",
            "%collection_id_%PatientID/%Modality/%StudyInstanceUID_%SeriesInstanceUID",
        ]
        for template in dirTemplateValues:
            with tempfile.TemporaryDirectory() as temp_dir:
                self.client.download_from_selection(
                    downloadDir=temp_dir,
                    studyInstanceUID="1.3.6.1.4.1.14519.5.2.1.7695.1700.114861588187429958687900856462",
                    dirTemplate=template,
                )
                self.assertEqual(
                    sum([len(files) for r, d, files in os.walk(temp_dir)]), 3
                )

    def test_download_from_selection(self):
        # Define the values for each optional parameter
        dry_run_values = [True, False]
        quiet_values = [True, False]
        show_progress_bar_values = [True, False]
        use_s5cmd_sync_values = [True, False]

        # Generate all combinations of optional parameters
        combinations = product(
            dry_run_values,
            quiet_values,
            show_progress_bar_values,
            use_s5cmd_sync_values,
        )

        # Test each combination
        for (
            dry_run,
            quiet,
            show_progress_bar,
            use_s5cmd_sync,
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

                if sum([len(files) for _, _, files in os.walk(temp_dir)]) != 9:
                    print(
                        f"Failed for {quiet} {validate_manifest} {show_progress_bar} {use_s5cmd_sync} {dirTemplate}"
                    )
                    self.assertFalse(True)

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

    """
    disabling these tests due to a consistent server timeout issue
    def test_citations(self):
        citations = self.client.citations_from_selection(
            collection_id="tcga_gbm",
            citation_format=index.IDCClient.CITATION_FORMAT_APA,
        )
        self.assertIsNotNone(citations)

        citations = self.client.citations_from_selection(
            seriesInstanceUID="1.3.6.1.4.1.14519.5.2.1.7695.4164.588007658875211151397302775781",
            citation_format=index.IDCClient.CITATION_FORMAT_BIBTEX,
        )
        self.assertIsNotNone(citations)

        citations = self.client.citations_from_selection(
            studyInstanceUID="1.2.840.113654.2.55.174144834924218414213677353968537663991",
            citation_format=index.IDCClient.CITATION_FORMAT_BIBTEX,
        )
        self.assertIsNotNone(citations)

        citations = self.client.citations_from_manifest("./study_manifest_aws.s5cmd")
        self.assertIsNotNone(citations)
    """

    def test_cli_download_from_selection(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(
                self.download_from_selection,
                [
                    "--download-dir",
                    temp_dir,
                    "--dry-run",
                    False,
                    "--quiet",
                    True,
                    "--show-progress-bar",
                    True,
                    "--use-s5cmd-sync",
                    False,
                    "--study-instance-uid",
                    "1.3.6.1.4.1.14519.5.2.1.7695.1700.114861588187429958687900856462",
                ],
            )
            assert len(os.listdir(temp_dir)) != 0

    def test_cli_download_from_manifest(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(
                self.download_from_manifest,
                [
                    "--manifest-file",
                    "./study_manifest_aws.s5cmd",
                    "--download-dir",
                    temp_dir,
                    "--quiet",
                    True,
                    "--show-progress-bar",
                    True,
                    "--use-s5cmd-sync",
                    False,
                ],
            )
            assert len(os.listdir(temp_dir)) != 0

    def test_singleton_attribute(self):
        # singleton, initialized on first use
        i1 = IDCClient.client()
        i2 = IDCClient.client()

        # new instances created via constructor (through init)
        i3 = IDCClient()
        i4 = self.client

        # all must be not none
        assert i1 is not None
        assert i2 is not None
        assert i3 is not None
        assert i4 is not None

        # singletons must return the same instance
        assert i1 == i2

        # new instances must be different
        assert i1 != i3
        assert i1 != i4
        assert i3 != i4

        # all must be instances of IDCClient
        assert isinstance(i1, IDCClient)
        assert isinstance(i2, IDCClient)
        assert isinstance(i3, IDCClient)
        assert isinstance(i4, IDCClient)

    def test_cli_download(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                self.download,
                # StudyInstanceUID:
                ["1.3.6.1.4.1.14519.5.2.1.7695.1700.114861588187429958687900856462"],
            )
            assert len(os.listdir(Path.cwd())) != 0

        with runner.isolated_filesystem():
            result = runner.invoke(
                self.download,
                # crdc_series_uuid:
                ["e5c5c71d-62c4-4c50-a8a9-b6799c7f8dea"],
            )
            assert len(os.listdir(Path.cwd())) != 0

    def test_prior_version_manifest(self):
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
                    manifestFile="./prior_version_manifest.s5cmd",
                    downloadDir=temp_dir,
                    quiet=quiet,
                    validate_manifest=validate_manifest,
                    show_progress_bar=show_progress_bar,
                    use_s5cmd_sync=use_s5cmd_sync,
                    dirTemplate=dirTemplate,
                )

                self.assertEqual(
                    sum([len(files) for r, d, files in os.walk(temp_dir)]), 5
                )

    def test_list_indices(self):
        i = IDCClient()
        assert i.indices_overview  # assert that dict was created

    def test_fetch_index(self):
        i = IDCClient()
        assert i.indices_overview["sm_index"]["installed"] is False
        i.fetch_index("sm_index")
        assert i.indices_overview["sm_index"]["installed"] is True
        assert hasattr(i, "sm_index")

    def test_indices_urls(self):
        i = IDCClient()
        for index in i.indices_overview:
            if i.indices_overview[index]["url"] is not None:
                assert remote_file_exists(i.indices_overview[index]["url"])


if __name__ == "__main__":
    unittest.main()
