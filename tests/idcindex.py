import unittest
import os
from idc_index import index
import tempfile
import logging

# Run tests using the following command from the root of the repository:
# python -m unittest -vv tests/idcindex.py

index.latest_index_url = 'https://github.com/ImagingDataCommons/idc-index/releases/download/latest/idc_index.csv.zip'

logging.basicConfig(level=logging.INFO)

class TestIDCClient(unittest.TestCase):
    def setUp(self):
        self.client = index.IDCClient()

        logger = logging.getLogger('idc_index')
        logger.setLevel(logging.DEBUG)

    def test_get_collections(self):
        collections = self.client.get_collections()
        self.assertIsNotNone(collections)

    def test_get_patients(self):
        patients = self.client.get_patients(collection_id="tcga_gbm", outputFormat="list")

        patients = self.client.get_patients(collection_id=["qin_prostate_repeatability","phantom_fda"], outputFormat="list")

        self.assertIsNotNone(patients)

    def test_get_studies(self):
        studies = self.client.get_dicom_studies(patientId="PCAMPMRI-00001", outputFormat="list")

        self.assertIsNotNone(studies)

        studies = self.client.get_dicom_studies(patientId=["PCAMPMRI-00001","NoduleLayout_1"], outputFormat="list")

        self.assertIsNotNone(studies)

    def test_get_series(self):
        series = self.client.get_dicom_series(studyInstanceUID="1.3.6.1.4.1.14519.5.2.1.6279.6001.175012972118199124641098335511", outputFormat="list")

        self.assertIsNotNone(series)

        series = self.client.get_dicom_series(studyInstanceUID=["1.3.6.1.4.1.14519.5.2.1.6279.6001.141365756818074696859567662357","1.3.6.1.4.1.14519.5.2.1.6279.6001.239368516910061467349404750170"], outputFormat="list")

        self.assertIsNotNone(series)

    def test_download_dicom_series(self):
        with tempfile.TemporaryDirectory() as temp_dir:
          self.client.download_dicom_series(seriesInstanceUID="1.3.6.1.4.1.14519.5.2.1.6279.6001.141365756818074696859567662357", downloadDir=temp_dir)
          self.assertNotEqual(len(os.listdir(temp_dir)),0)

    def test_download_from_selection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
          self.client.download_from_selection(studyInstanceUID="1.3.6.1.4.1.14519.5.2.1.6279.6001.175012972118199124641098335511", downloadDir=temp_dir)

          self.assertNotEqual(len(os.listdir(temp_dir)),0)

    def test_sql_queries(self):
        df = self.client.sql_query("SELECT DISTINCT(collection_id) FROM index")

        self.assertIsNotNone(df)

    def test_download_from_aws_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
          self.client.download_from_manifest(manifestFile="./tests/study_manifest_aws.s5cmd", downloadDir=temp_dir)

          self.assertEqual(len(os.listdir(temp_dir)), 15)

    def test_download_from_gcp_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
          self.client.download_from_manifest(manifestFile="./tests/study_manifest_gcs.s5cmd", downloadDir=temp_dir)

          self.assertEqual(len(os.listdir(temp_dir)),15)

if __name__ == '__main__':
    unittest.main()