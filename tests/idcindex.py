import unittest
import os
from idc_index import index
import tempfile

class TestIDCClient(unittest.TestCase):
    def setUp(self):
        self.client = index.IDCClient()

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
        series = self.client.get_dicom_series(studyInstanceUID="1.3.6.1.4.1.14519.5.2.1.3671.4754.288848219213026850354055725664", outputFormat="list")

        self.assertIsNotNone(series)

        series = self.client.get_dicom_series(studyInstanceUID=["1.3.6.1.4.1.14519.5.2.1.3671.4754.288848219213026850354055725664","1.2.840.113704.1.111.2408.1187360342.8"], outputFormat="list")

        self.assertIsNotNone(series)

    def test_download_dicom_series(self):
        with tempfile.TemporaryDirectory() as temp_dir:
          self.client.download_dicom_series(seriesInstanceUID="1.2.840.113704.1.111.3972.1187368426.50", downloadDir=temp_dir)
          self.assertIsNotNone(os.listdir(temp_dir))

    def test_download_from_selection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
          self.client.download_from_selection(studyInstanceUID="1.3.6.1.4.1.14519.5.2.1.3320.3273.234458321320456015460025860862", downloadDir=temp_dir)

          self.assertIsNotNone(os.listdir(temp_dir))

    def test_sql_queries(self):
        df = self.client.sql_query("SELECT DISTINCT(collection_id) FROM index")

        self.assertIsNotNone(df)
if __name__ == '__main__':
    unittest.main()