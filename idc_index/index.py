# pylint: disable=too-many-lines

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
import time
from importlib.metadata import distribution
from pathlib import Path

import duckdb
import idc_index_data
import pandas as pd
import psutil
import requests
from packaging.version import Version
from tqdm import tqdm

aws_endpoint_url = "https://s3.amazonaws.com"
gcp_endpoint_url = "https://storage.googleapis.com"
asset_endpoint_url = f"https://github.com/ImagingDataCommons/idc-index-data/releases/download/{idc_index_data.__version__}"

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


class IDCClient:
    # Default download hierarchy template
    DOWNLOAD_HIERARCHY_DEFAULT = (
        "%collection_id/%PatientID/%StudyInstanceUID/%Modality_%SeriesInstanceUID"
    )

    # Defined citation formats that can be passed to the citations request methods
    # see acceptable values at https://citation.crosscite.org/docs.html#sec-4
    CITATION_FORMAT_APA = "text/x-bibliography; style=apa; locale=en-US"
    CITATION_FORMAT_TURTLE = "text/turtle"
    CITATION_FORMAT_JSON = "application/vnd.citationstyles.csl+json"
    CITATION_FORMAT_BIBTEX = "application/x-bibtex"

    # Singleton pattern
    # NOTE: In the future, one may want to use multiple clients e.g. for sub-datasets so a attribute-singleton as shown below seems a better option.
    # _instance: IDCClient
    # def __new__(cls):
    #     if not hasattr(cls, "_instance") or getattr(cls, "_instance") is None:
    #         instance = super(IDCClient, cls).__new__(cls)
    #         setattr(cls, "_instance", instance)
    #     return cls._instance

    _client: IDCClient

    @classmethod
    def client(cls) -> IDCClient:
        if not hasattr(cls, "_client") or getattr(cls, "_client") is None:
            setattr(cls, "_client", IDCClient())

        return cls._client

    def __init__(self):
        # Read main index file
        file_path = idc_index_data.IDC_INDEX_PARQUET_FILEPATH
        logger.debug(f"Reading index file v{idc_index_data.__version__}")
        self.index = pd.read_parquet(file_path)

        # initialize crdc_series_uuid for the index
        # TODO: in the future, after https://github.com/ImagingDataCommons/idc-index/pull/113
        # is merged (to minimize disruption), it will make more sense to change
        # idc-index-data to separate bucket from crdc_series_uuid, add support for GCP,
        # and consequently simplify the code here
        self.index["crdc_series_uuid"] = (
            self.index["series_aws_url"].str.split("/").str[3]
        )

        self.previous_versions_index_path = (
            idc_index_data.PRIOR_VERSIONS_INDEX_PARQUET_FILEPATH
        )
        file_path = idc_index_data.PRIOR_VERSIONS_INDEX_PARQUET_FILEPATH

        self.previous_versions_index = pd.read_parquet(file_path)

        # self.index = self.index.astype(str).replace("nan", "")
        self.index["series_size_MB"] = self.index["series_size_MB"].astype(float)
        self.collection_summary = self.index.groupby("collection_id").agg(
            {"Modality": pd.Series.unique, "series_size_MB": "sum"}
        )

        idc_version = f"v{Version(idc_index_data.__version__).major}"

        self.indices_overview = {
            "index": {
                "description": "Main index containing one row per DICOM series.",
                "installed": True,
                "url": None,
            },
            "previous_versions_index": {
                "description": "index containing one row per DICOM series from all previous IDC versions that are not in current version.",
                "installed": True,
                "url": None,
            },
            "sm_index": {
                "description": "DICOM Slide Microscopy series-level index.",
                "installed": False,
                "url": f"{asset_endpoint_url}/sm_index.parquet",
            },
            "sm_instance_index": {
                "description": "DICOM Slide Microscopy instance-level index.",
                "installed": False,
                "url": f"{asset_endpoint_url}/sm_instance_index.parquet",
            },
            "clinical_index": {
                "description": "Index of clinical data accompanying the available images.",
                "installed": False,
                "url": f"{asset_endpoint_url}/clinical_index.parquet",
            },
        }

        # Lookup s5cmd
        self.s5cmdPath = shutil.which("s5cmd")
        if self.s5cmdPath is None:
            # Workaround to support environment without a properly setup PATH
            # See https://github.com/Slicer/Slicer/pull/7587
            logger.debug("Falling back to looking up s5cmd along side the package")
            for script in distribution("s5cmd").files:
                if str(script).startswith("s5cmd/bin/s5cmd"):
                    self.s5cmdPath = script.locate().resolve(strict=True)
                    break
        if self.s5cmdPath is None:
            raise FileNotFoundError(
                "s5cmd executable not found. Please install s5cmd from https://github.com/peak/s5cmd#installation"
            )
        self.s5cmdPath = str(self.s5cmdPath)
        logger.debug(f"Found s5cmd executable: {self.s5cmdPath}")
        # ... and check it can be executed
        subprocess.check_call([self.s5cmdPath, "--help"], stdout=subprocess.DEVNULL)

    @staticmethod
    def _filter_dataframe_by_id(key, dataframe, _id):
        values = _id
        if isinstance(_id, str):
            values = [_id]
        filtered_df = dataframe[dataframe[key].isin(values)].copy()
        if filtered_df.empty:
            error_message = f"No data found for the {key} with the values {values}."
            raise ValueError(error_message)
        return filtered_df

    @staticmethod
    def _safe_filter_by_selection(
        df_index,
        collection_id,
        patientId,
        studyInstanceUID,
        seriesInstanceUID,
        sopInstanceUID,
        crdc_series_uuid,
    ):
        if collection_id is not None:
            if not isinstance(collection_id, str) and not isinstance(
                collection_id, list
            ):
                raise TypeError("collection_id must be a string or list of strings")
        if patientId is not None:
            if not isinstance(patientId, str) and not isinstance(patientId, list):
                raise TypeError("patientId must be a string or list of strings")
        if studyInstanceUID is not None:
            if not isinstance(studyInstanceUID, str) and not isinstance(
                studyInstanceUID, list
            ):
                raise TypeError("studyInstanceUID must be a string or list of strings")
        if seriesInstanceUID is not None:
            if not isinstance(seriesInstanceUID, str) and not isinstance(
                seriesInstanceUID, list
            ):
                raise TypeError("seriesInstanceUID must be a string or list of strings")
        if sopInstanceUID is not None:
            if not isinstance(sopInstanceUID, str) and not isinstance(
                sopInstanceUID, list
            ):
                raise TypeError("sopInstanceUID must be a string or list of strings")

        if crdc_series_uuid is not None:
            if not isinstance(crdc_series_uuid, str) and not isinstance(
                crdc_series_uuid, list
            ):
                raise TypeError("crdc_series_uuid must be a string or list of strings")

        # Here we go down-up the hierarchy of filtering, taking into
        # account the direction of one-to-many relationships
        #   one crdc_series_uuid can be associated with one and only one SeriesInstanceUID
        #   one SeriesInstanceUID can be associated with one and only one StudyInstanceUID
        #   one StudyInstanceUID can be associated with one and only one PatientID
        #   one PatientID can be associated with one and only one collection_id
        # because of this we do not need to apply attributes above the given defined
        # attribute in the hierarchy
        # The earlier implemented behavior was a relic of the API from a different system
        # that influenced the API of SlicerIDCIndex, and propagated into idc-index. Unfortunately.

        if crdc_series_uuid is not None:
            result_df = IDCClient._filter_dataframe_by_id(
                "crdc_series_uuid", df_index, crdc_series_uuid
            )
            return result_df

        if sopInstanceUID is not None:
            result_df = IDCClient._filter_by_dicom_instance_uid(
                df_index, sopInstanceUID
            )
            return result_df

        if seriesInstanceUID is not None:
            result_df = IDCClient._filter_by_dicom_series_uid(
                df_index, seriesInstanceUID
            )
            return result_df

        if studyInstanceUID is not None:
            result_df = IDCClient._filter_by_dicom_study_uid(df_index, studyInstanceUID)
            return result_df

        if patientId is not None:
            result_df = IDCClient._filter_by_patient_id(df_index, patientId)
            return result_df

        if collection_id is not None:
            result_df = IDCClient._filter_by_collection_id(df_index, collection_id)
            return result_df

        return None

    @staticmethod
    def _filter_by_collection_id(df_index, collection_id):
        return IDCClient._filter_dataframe_by_id(
            "collection_id", df_index, collection_id
        )

    @staticmethod
    def _filter_by_patient_id(df_index, patient_id):
        return IDCClient._filter_dataframe_by_id("PatientID", df_index, patient_id)

    @staticmethod
    def _filter_by_dicom_study_uid(df_index, dicom_study_uid):
        return IDCClient._filter_dataframe_by_id(
            "StudyInstanceUID", df_index, dicom_study_uid
        )

    @staticmethod
    def _filter_by_dicom_series_uid(df_index, dicom_series_uid):
        return IDCClient._filter_dataframe_by_id(
            "SeriesInstanceUID", df_index, dicom_series_uid
        )

    @staticmethod
    def _filter_by_dicom_instance_uid(df_index, dicom_instance_uid):
        return IDCClient._filter_dataframe_by_id(
            "SOPInstanceUID", df_index, dicom_instance_uid
        )

    @staticmethod
    def get_idc_version():
        """
        Returns the version of IDC data used in idc-index
        """
        idc_version = Version(idc_index_data.__version__).major
        return f"v{idc_version}"

    @staticmethod
    def _check_create_directory(download_dir):
        """
        Mimic behavior of s5cmd and create the download directory if it does not exist
        """
        download_dir = Path(download_dir)
        download_dir.mkdir(parents=True, exist_ok=True)

        return str(download_dir.resolve())

    def fetch_index(self, index) -> None:
        """
        Downloads requested index and adds this index joined with the main index as respective class attribute.

        Args:
            index (str): Name of the index to be downloaded.
        """

        if index not in self.indices_overview:
            logger.error(f"Index {index} is not available and can not be fetched.")
        elif self.indices_overview[index]["installed"]:
            logger.warning(
                f"Index {index} already installed and will not be fetched again."
            )
        else:
            response = requests.get(self.indices_overview[index]["url"], timeout=30)
            if response.status_code == 200:
                filepath = os.path.join(
                    idc_index_data.IDC_INDEX_PARQUET_FILEPATH.parents[0],
                    f"{index}.parquet",
                )

                with open(filepath, mode="wb") as file:
                    file.write(response.content)

                index_table = pd.read_parquet(filepath)
                # index_table = index_table.merge(
                #    self.index[["series_aws_url", "SeriesInstanceUID"]],
                #    on="SeriesInstanceUID", how="left"
                # )
                setattr(self.__class__, index, index_table)
                self.indices_overview[index]["installed"] = True

            else:
                logger.error(
                    f"Failed to fetch index from URL {self.indices_overview[index]['url']}: {response.status_code}"
                )

    def get_collections(self):
        """
        Returns the collections present in IDC
        """
        unique_collections = self.index["collection_id"].unique()
        return unique_collections.tolist()

    def get_series_size(self, seriesInstanceUID):
        """
        Gets cumulative size (MB) of the DICOM instances in a given SeriesInstanceUID.

        Args:
            seriesInstanceUID (str): The DICOM SeriesInstanceUID.

        Returns:
            float: The cumulative size of the DICOM instances in the given SeriesInstanceUID rounded to two digits, in MB.

        Raises:
            ValueError: If the `seriesInstanceUID` does not exist.
        """

        resp = self.index[["SeriesInstanceUID"] == seriesInstanceUID][
            "series_size_MB"
        ].iloc[0]
        return resp

    def get_patients(self, collection_id, outputFormat="dict"):
        """
        Gets the patients in a collection.

        Args:
            collection_id (str or list[str]): The collection id or list of collection ids. This should be in lower case separated by underscores.
                For example, 'pdmr_texture_analysis'. or ['pdmr_texture_analysis','nlst']

            outputFormat (str): The format in which to return the patient IDs. Available options are 'dict',
                'df', and 'list'. Default is 'dict'.

        Returns:
            dict or pandas.DataFrame or list: Patient IDs in the requested output format. By default, it returns a dictionary.

        Raises:
            ValueError: If `outputFormat` is not one of 'dict', 'df', 'list'.
        """

        if not isinstance(collection_id, str) and not isinstance(collection_id, list):
            raise TypeError("collection_id must be a string or list of strings")

        if outputFormat not in ["dict", "df", "list"]:
            raise ValueError("outputFormat must be either 'dict', 'df', or 'list")

        patient_df = self._filter_by_collection_id(self.index, collection_id)

        if outputFormat == "list":
            response = patient_df["PatientID"].unique().tolist()
        else:
            sql = """
                SELECT
                    PatientID,
                    STRING_AGG(DISTINCT PatientSex) as PatientSex,
                    STRING_AGG(DISTINCT PatientAge) as PatientAge
                FROM
                    patient_df
                GROUP BY
                    PatientID
                ORDER BY
                    PatientID
                """
            patient_df = duckdb.sql(sql).df()
            # Convert DataFrame to a list of dictionaries for the API-like response
            if outputFormat == "dict":
                response = patient_df.to_dict(orient="records")
            else:
                response = patient_df

        logger.debug("Get patient response: %s", str(response))

        return response

    def get_dicom_studies(self, patientId, outputFormat="dict"):
        """
        Returns Studies for a given patient or list of patients.

        Args:
            patientId (str or list of str): The patient Id or a list of patient Ids.

            outputFormat (str): The format in which to return the studies. Available options are 'dict',
                'df', and 'list'. Default is 'dict'.

        Returns:
            dict or pandas.DataFrame or list: Studies in the requested output format. By default, it returns a dictionary.

        Raises:
            ValueError: If `outputFormat` is not one of 'dict', 'df', 'list'.
            ValueError: If any of the `patientId` does not exist.
        """

        if not isinstance(patientId, str) and not isinstance(patientId, list):
            raise TypeError("patientId must be a string or list of strings")

        if outputFormat not in ["dict", "df", "list"]:
            raise ValueError("outputFormat must be either 'dict' or 'df' or 'list'")

        studies_df = self._filter_by_patient_id(self.index, patientId)

        if outputFormat == "list":
            response = studies_df["StudyInstanceUID"].unique().tolist()
        else:
            sql = """
                SELECT
                    StudyInstanceUID,
                    STRING_AGG(DISTINCT StudyDate) as StudyDate,
                    STRING_AGG(DISTINCT StudyDescription) as StudyDescription,
                    COUNT(SeriesInstanceUID) as SeriesCount
                FROM
                    studies_df
                GROUP BY
                    StudyInstanceUID
                ORDER BY
                    2,3,4
                """
            studies_df = duckdb.query(sql).df()

            if outputFormat == "dict":
                response = studies_df.to_dict(orient="records")
            else:
                response = studies_df

        logger.debug("Get patient study response: %s", str(response))

        return response

    def get_dicom_series(self, studyInstanceUID, outputFormat="dict"):
        """
        Returns Series for a given study or list of studies.

        Args:
            studyInstanceUID (str or list of str): The DICOM StudyInstanceUID or a list of StudyInstanceUIDs.

            outputFormat (str): The format in which to return the series. Available options are 'dict',
                'df', and 'list'. Default is 'dict'.

        Returns:
            dict or pandas.DataFrame or list: Series in the requested output format. By default, it returns a dictionary.

        Raises:
            ValueError: If `outputFormat` is not one of 'dict', 'df', 'list'.
            ValueError: If any of the `studyInstanceUID` does not exist.
        """

        if not isinstance(studyInstanceUID, str) and not isinstance(
            studyInstanceUID, list
        ):
            raise TypeError("studyInstanceUID must be a string or list of strings")

        if outputFormat not in ["dict", "df", "list"]:
            raise ValueError("outputFormat must be either 'dict' or 'df' or 'list'")

        series_df = self._filter_by_dicom_study_uid(self.index, studyInstanceUID)

        if outputFormat == "list":
            response = series_df["SeriesInstanceUID"].unique().tolist()
        else:
            series_df = series_df.rename(
                columns={
                    "collection_id": "Collection",
                    "instanceCount": "instance_count",
                }
            )
            series_df["ImageCount"] = 1
            series_df = series_df[
                [
                    "StudyInstanceUID",
                    "SeriesInstanceUID",
                    "Modality",
                    "SeriesDate",
                    "Collection",
                    "BodyPartExamined",
                    "SeriesDescription",
                    "Manufacturer",
                    "ManufacturerModelName",
                    "series_size_MB",
                    "SeriesNumber",
                    "instance_count",
                    "ImageCount",
                ]
            ]

            series_df = series_df.drop_duplicates().sort_values(
                by=[
                    "Modality",
                    "SeriesDate",
                    "SeriesDescription",
                    "BodyPartExamined",
                    "SeriesNumber",
                ]
            )
            # Convert DataFrame to a list of dictionaries for the API-like response
            if outputFormat == "dict":
                response = series_df.to_dict(orient="records")
            else:
                response = series_df
        logger.debug("Get series response: %s", str(response))

        return response

    def get_series_file_URLs(self, seriesInstanceUID):
        """
        Get the URLs of the files corresponding to the DICOM instances in a given SeriesInstanceUID.

        Args:
            SeriesInstanceUID: string containing the value of DICOM SeriesInstanceUID to filter by

        Returns:
            list of strings containing the AWS S3 URLs of the files corresponding to the SeriesInstanceUID
        """
        # Query to get the S3 URL
        s3url_query = f"""
        SELECT
        series_aws_url
        FROM
        index
        WHERE
        SeriesInstanceUID='{seriesInstanceUID}'
        """
        s3url_query_df = self.sql_query(s3url_query)
        s3_url = s3url_query_df.series_aws_url[0]

        # Remove the last character from the S3 URL
        s3_url = s3_url[:-1]

        # Run the s5cmd ls command and capture its output
        result = subprocess.run(
            [self.s5cmdPath, "--no-sign-request", "ls", s3_url],
            stdout=subprocess.PIPE,
            check=False,
        )
        output = result.stdout.decode("utf-8")

        # Parse the output to get the file names
        lines = output.split("\n")
        file_names = [
            s3_url + line.split()[-1]
            for line in lines
            if line and line.split()[-1].endswith(".dcm")
        ]

        return file_names

    def get_viewer_URL(
        self, seriesInstanceUID=None, studyInstanceUID=None, viewer_selector=None
    ):
        """
        Get the URL of the IDC viewer for the given series or study in IDC based on
        the provided SeriesInstanceUID or StudyInstanceUID. If StudyInstanceUID is not provided,
        it will be automatically deduced. If viewer_selector is not provided, default viewers
        will be used (OHIF v2 or v3 for radiology modalities, and Slim for SM).

        This function will validate the provided SeriesInstanceUID or StudyInstanceUID against IDC
        index to ensure that the series or study is available in IDC.

        Args:
            SeriesInstanceUID: string containing the value of DICOM SeriesInstanceUID for a series
                available in IDC

            StudyInstanceUID: string containing the value of DICOM SeriesInstanceUID for a series
                available in IDC

            viewer_selector: string containing the name of the viewer to use. Must be one of the following:
                ohif_v2, ohif_v3, or slim. If not provided, default viewers will be used.

        Returns:
            string containing the IDC viewer URL for the requested selection
        """

        if seriesInstanceUID is None and studyInstanceUID is None:
            raise ValueError(
                "Either SeriesInstanceUID or StudyInstanceUID, or both, must be provided."
            )

        if (
            seriesInstanceUID is not None
            and seriesInstanceUID not in self.index["SeriesInstanceUID"].values
        ):
            raise ValueError("SeriesInstanceUID not found in IDC index.")

        if (
            studyInstanceUID is not None
            and studyInstanceUID not in self.index["StudyInstanceUID"].values
        ):
            raise ValueError("StudyInstanceUID not found in IDC index.")

        if viewer_selector is not None and viewer_selector not in [
            "ohif_v2",
            "ohif_v3",
            "slim",
        ]:
            raise ValueError(
                "viewer_selector must be one of 'ohif_v2', 'ohif_v3',  or 'slim'."
            )

        modality = None

        if studyInstanceUID is None:
            query = f"""
            SELECT
                DISTINCT(StudyInstanceUID),
                Modality
            FROM
                index
            WHERE
                SeriesInstanceUID='{seriesInstanceUID}'
            """
            query_result = self.sql_query(query)
            studyInstanceUID = query_result.StudyInstanceUID[0]
            modality = query_result.Modality[0]

        else:
            query = f"""
            SELECT
                DISTINCT(Modality)
            FROM
                index
            WHERE
                StudyInstanceUID='{studyInstanceUID}'
            """
            query_result = self.sql_query(query)
            modality = query_result.Modality[0]

        viewer_url = None
        if viewer_selector is None:
            if "SM" in modality:
                viewer_selector = "slim"
            else:
                viewer_selector = "ohif_v2"

        if viewer_selector == "ohif_v2":
            if seriesInstanceUID is None:
                viewer_url = f"https://viewer.imaging.datacommons.cancer.gov/viewer/{studyInstanceUID}"
            else:
                viewer_url = f"https://viewer.imaging.datacommons.cancer.gov/viewer/{studyInstanceUID}?SeriesInstanceUID={seriesInstanceUID}"
        elif viewer_selector == "ohif_v3":
            if seriesInstanceUID is None:
                viewer_url = f"https://viewer.imaging.datacommons.cancer.gov/v3/viewer/?StudyInstanceUIDs={studyInstanceUID}"
            else:
                viewer_url = f"https://viewer.imaging.datacommons.cancer.gov/v3/viewer/?StudyInstanceUIDs={studyInstanceUID}&SeriesInstanceUIDs={seriesInstanceUID}"
        elif viewer_selector == "volview":
            # TODO! Not implemented yet
            viewer_url = None
        elif viewer_selector == "slim":
            if seriesInstanceUID is None:
                viewer_url = f"https://viewer.imaging.datacommons.cancer.gov/slim/studies/{studyInstanceUID}"
            else:
                viewer_url = f"https://viewer.imaging.datacommons.cancer.gov/slim/studies/{studyInstanceUID}/series/{seriesInstanceUID}"

        return viewer_url

    def _validate_update_manifest_and_get_download_size(
        self,
        manifestFile,
        downloadDir,
        validate_manifest,
        use_s5cmd_sync,
        dirTemplate,
    ) -> tuple[float, str, Path]:
        """
        Validates the manifest file by checking the URLs in the manifest

        Args:
            manifestFile (str): The path to the manifest file.
            downloadDir (str): The path to the download directory.
            validate_manifest (bool): If True, validates the manifest for any errors. Defaults to True.
            show_progress_bar (bool): If True, tracks the progress of download
            use_s5cmd_sync (bool): If True, will use s5cmd sync operation instead of cp when downloadDirectory is not empty; this can significantly improve the download speed if the content is partially downloaded
            dirTemplate (str): A template string for the directory path. Must start with %. Defaults to index.DOWNLOAD_HIERARCHY_DEFAULT. It can contain attributes (PatientID, collection_id, Modality, StudyInstanceUID, SeriesInstanceUID) wrapped in '%'. Special characters can be used as connectors: '-' (hyphen), '/' (slash for subdirectories), '_' (underscore). Can be disabled by None.

        Returns:
            total_size (float): The total size of all series in the manifest file.
            endpoint_to_use (str): The endpoint URL to use (either AWS or GCP).
            temp_manifest_file(Path): Path to the temporary manifest file for downstream steps
        Raises:
            ValueError: If the manifest file does not exist, if any URL in the manifest file is invalid, or if any URL is inaccessible in both AWS and GCP.
            Exception: If the manifest contains URLs from both AWS and GCP.
        """
        logger.debug("manifest validation is requested: " + str(validate_manifest))

        logger.debug("Parsing the manifest. Please wait..")
        # Read the manifest as a csv file
        manifest_df = pd.read_csv(
            manifestFile, comment="#", skip_blank_lines=True, header=None
        )

        # Rename the column
        manifest_df.columns = ["manifest_cp_cmd"]

        # create a copy of the index
        index_df_copy = self.index[
            [
                "SeriesInstanceUID",
                "series_aws_url",
                "series_size_MB",
                "PatientID",
                "collection_id",
                "Modality",
                "StudyInstanceUID",
            ]
        ]
        previous_versions_index_df_copy = self.previous_versions_index[
            [
                "SeriesInstanceUID",
                "series_aws_url",
                "series_size_MB",
                "PatientID",
                "collection_id",
                "Modality",
                "StudyInstanceUID",
            ]
        ]

        # use default hierarchy
        if dirTemplate is not None:
            hierarchy = self._generate_sql_concat_for_building_directory(
                dirTemplate=dirTemplate, downloadDir=downloadDir
            )
        else:
            hierarchy = f"CONCAT('{downloadDir}')"

        # Extract s3 url and crdc_series_uuid from the manifest copy commands
        # Next, extract crdc_series_uuid from aws_series_url in the index and
        # try to verify if every series in the manifest is present in the index

        # TODO: need to remove the assumption that manifest commands will have 'cp'
        #  and need to parse S3 URL directly
        # ruff: noqa
        sql = f"""
            PRAGMA disable_progress_bar;
            WITH
            index_temp AS (
            SELECT
                seriesInstanceUID,
                series_aws_url,
                series_size_MB,
                {hierarchy} AS path,
                REGEXP_EXTRACT(series_aws_url, '(?:.*?\\/){{3}}([^\\/?#]+)', 1) index_crdc_series_uuid
            FROM
                index_df_copy),
            manifest_temp AS (
            SELECT
                manifest_cp_cmd,
                REGEXP_EXTRACT(manifest_cp_cmd, '(?:.*?\\/){{3}}([^\\/?#]+)', 1) AS manifest_crdc_series_uuid,
                REGEXP_EXTRACT(manifest_cp_cmd, 's3://\\S+') AS s3_url,
            FROM
                manifest_df )
            SELECT
                seriesInstanceuid,
                index_crdc_series_uuid,
                s3_url,
                path,
                series_size_MB,
                index_crdc_series_uuid is not NULL as crdc_series_uuid_match,
                s3_url==series_aws_url AS s3_url_match,
                manifest_temp.manifest_cp_cmd,
            CASE
                WHEN s3_url==series_aws_url THEN 'aws'
            ELSE
                'unknown'
            END
                AS endpoint
            FROM
                manifest_temp
            LEFT JOIN
                index_temp
            ON
                index_temp.index_crdc_series_uuid = manifest_temp.manifest_crdc_series_uuid
        """
        # ruff: noqa: end
        merged_df = duckdb.query(sql).df()

        endpoint_to_use = None

        if not all(merged_df["crdc_series_uuid_match"]):
            missing_manifest_cp_cmds = merged_df.loc[
                ~merged_df["crdc_series_uuid_match"], "manifest_cp_cmd"
            ]
            missing_in_main_cnt = len(missing_manifest_cp_cmds.tolist())
            logger.warning(
                f"The total of {missing_in_main_cnt} copy commands are not recognized as referencing any associated series in the main index.\n"
                "This means either these commands are invalid, or they may correspond to files available in a release of IDC\n"
                f"different from {self.get_idc_version()} used in this version of idc-index. Prior data releases will be checked next."
            )

            logger.debug(
                "Checking if the requested data is available in other idc versions "
            )
            missing_series_sql = f"""
            PRAGMA disable_progress_bar;
            WITH
            combined_index AS
            (SELECT
                 seriesInstanceUID,
                series_aws_url,
                series_size_MB,
                {hierarchy} AS path,
            FROM
                index_df_copy
            union by name
            SELECT
                seriesInstanceUID,
                series_aws_url,
                series_size_MB,
                 {hierarchy} AS path,
            FROM
                previous_versions_index_df_copy pvip

            ),
            index_temp AS (
            SELECT
                seriesInstanceUID,
                series_aws_url,
                series_size_MB,
                path,
                REGEXP_EXTRACT(series_aws_url, '(?:.*?\\/){{3}}([^\\/?#]+)', 1) index_crdc_series_uuid
            FROM
                combined_index),
            manifest_temp AS (
            SELECT
                manifest_cp_cmd,
                REGEXP_EXTRACT(manifest_cp_cmd, '(?:.*?\\/){{3}}([^\\/?#]+)', 1) AS manifest_crdc_series_uuid,
                REGEXP_REPLACE(regexp_replace(manifest_cp_cmd, 'cp ', ''), '\\s[^\\s]*$', '') AS s3_url,
            FROM
                manifest_df )
            SELECT
                seriesInstanceuid,
                index_crdc_series_uuid,
                s3_url,
                path,
                series_size_MB,
                index_crdc_series_uuid is not NULL as crdc_series_uuid_match,
                TRIM(s3_url) = TRIM(series_aws_url) AS s3_url_match,
                manifest_temp.manifest_cp_cmd,
            CASE
                WHEN TRIM(s3_url) = TRIM(series_aws_url) THEN 'aws'
            ELSE
                'unknown'
            END
                AS endpoint
            FROM
                manifest_temp
            LEFT JOIN
                index_temp
            ON
                index_temp.index_crdc_series_uuid = manifest_temp.manifest_crdc_series_uuid
            """
            merged_df = duckdb.sql(missing_series_sql).df()
            if not all(merged_df["crdc_series_uuid_match"]):
                missing_manifest_cp_cmds = merged_df.loc[
                    ~merged_df["crdc_series_uuid_match"], "manifest_cp_cmd"
                ]
                logger.error(
                    "The following manifest copy commands are not recognized as referencing any associated series in any release of IDC.\n"
                    "These commands may be invalid. Please submit an issue on https://github.com/ImagingDataCommons/idc-index/issues \n"
                    "The corresponding files could not be downloaded.\n"
                )
                logger.error("\n" + "\n".join(missing_manifest_cp_cmds.tolist()))
            else:
                logger.info("All of the identifiers from manifest have been resolved!")

        if validate_manifest:
            # Check if there is more than one endpoint
            if len(merged_df["endpoint"].unique()) > 1:
                raise ValueError(
                    "Either GCS bucket path is invalid or manifest has a mix of GCS and AWS urls. "
                )

            if (
                len(merged_df["endpoint"].unique()) == 1
                and merged_df["endpoint"].values[0] == "aws"
            ):
                endpoint_to_use = aws_endpoint_url

            if (
                len(merged_df["endpoint"].unique()) == 1
                and merged_df["endpoint"].values[0] == "unknown"
            ):
                cmd = [
                    self.s5cmdPath,
                    "--no-sign-request",
                    "--endpoint-url",
                    gcp_endpoint_url,
                    "ls",
                    merged_df.s3_url.values[0],
                ]
                process = subprocess.run(
                    cmd, capture_output=True, text=True, check=False
                )
                if process.stderr and process.stdout.startswith("ERROR"):
                    logger.debug(
                        "Folder not available in GCP. Manifest appears to be invalid."
                    )
                    if validate_manifest:
                        raise ValueError
                else:
                    endpoint_to_use = gcp_endpoint_url

        elif merged_df["endpoint"].values[0] == "aws":
            endpoint_to_use = aws_endpoint_url
        else:
            # TODO: here we assume that the endpoint is GCP; we could check at least the first URL to be sure,
            # but we can take care of this in a more principled way by including GCP bucket directly
            # in the future, see https://github.com/ImagingDataCommons/idc-index/pull/56#discussion_r1582157048
            endpoint_to_use = gcp_endpoint_url

        # Calculate total size
        total_size = merged_df["series_size_MB"].sum()
        total_size = round(total_size, 2)

        # Write a temporary manifest file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_manifest_file:
            if use_s5cmd_sync and len(os.listdir(downloadDir)) != 0:
                if dirTemplate is not None:
                    merged_df["s5cmd_cmd"] = (
                        "sync "
                        + merged_df["s3_url"]
                        + " "
                        + '"'
                        + merged_df["path"]
                        + '"'
                    )
                else:
                    merged_df["s5cmd_cmd"] = (
                        "sync " + merged_df["s3_url"] + " " + '"' + downloadDir + '"'
                    )
            elif dirTemplate is not None:
                merged_df["s5cmd_cmd"] = (
                    "cp " + merged_df["s3_url"] + " " + '"' + merged_df["path"] + '"'
                )
            else:
                merged_df["s5cmd_cmd"] = (
                    "cp " + merged_df["s3_url"] + " " + '"' + downloadDir + '"'
                )

            # Combine all commands into a single string with newline separators
            commands = "\n".join(merged_df["s5cmd_cmd"])

            temp_manifest_file.write(commands)

            logger.info("Parsing the manifest is finished. Download will begin soon")

        if dirTemplate is not None:
            list_of_directories = merged_df.path.to_list()
        else:
            list_of_directories = [downloadDir]

        logger.debug(f"list of directories:{list_of_directories}")
        return (
            total_size,
            endpoint_to_use,
            Path(temp_manifest_file.name),
            list_of_directories,
            merged_df[
                ["index_crdc_series_uuid", "s5cmd_cmd", "series_size_MB", "path"]
            ],
        )

    @staticmethod
    def _generate_sql_concat_for_building_directory(dirTemplate, downloadDir):
        # for now, we limit the allowed columns to this list to make sure that all
        # values are guaranteed to be non-empty and to not contain any special characters
        # in the future, we should consider including more attributes
        # also, if we allow any column, we should decide what we would do if the value is NULL
        valid_attributes = [
            "PatientID",
            "collection_id",
            "Modality",
            "StudyInstanceUID",
            "SeriesInstanceUID",
        ]
        valid_separators = ["_", "-", "/"]

        updated_template = dirTemplate

        # validate input template by removing all valid attributes and separators
        for attr in valid_attributes:
            updated_template = updated_template.replace("%" + attr, "")
        for sep in valid_separators:
            updated_template = updated_template.replace(sep, "")

        if updated_template != "":
            logger.error("Invalid download hierarchy template:" + updated_template)
            logger.error(
                "Make sure your template uses only valid attributes and separators"
            )
            logger.error("Valid attributes: " + str(valid_attributes))
            logger.error("Valid separators: " + str(valid_separators))
            raise ValueError

        concat_command = dirTemplate
        for attr in valid_attributes:
            concat_command = concat_command.replace("%" + attr, f"', {attr},'")

        # CONCAT command may contain empty strings, and they are not harmless -
        # duckdb does not like them!
        # NB: double-quotes are not allowed by duckdb!
        concat_command = f"CONCAT('{downloadDir}/','" + concat_command + "')"
        concat_command = concat_command.replace(",''", "")
        concat_command = concat_command.replace("'',", "")
        concat_command = concat_command.replace(",'',", "")
        return concat_command

    @staticmethod
    def _track_download_progress(
        size_MB: int,
        downloadDir: str,
        process: subprocess.Popen,
        show_progress_bar: bool = True,
        list_of_directories=None,
    ):
        logger.debug("Inputs received for tracking download:")
        logger.debug(f"size_MB: {size_MB}")
        logger.debug(f"downloadDir: {downloadDir}")
        logger.debug(f"show_progress_bar: {show_progress_bar}")

        runtime_errors = []

        if show_progress_bar:
            total_size_to_be_downloaded_bytes = size_MB * (10**6)
            initial_size_bytes = 0
            # Calculate the initial size of the directory
            for directory in list_of_directories:
                initial_size_bytes = IDCClient._get_dir_sum_file_size(directory)

            logger.info(
                "Initial size of the directory: %s",
                IDCClient._format_size(initial_size_bytes, size_in_bytes=True),
            )
            logger.info(
                "Approximate size of the files that need to be downloaded: %s",
                IDCClient._format_size(size_MB),
            )

            pbar = tqdm(
                total=total_size_to_be_downloaded_bytes,
                unit="B",
                unit_scale=True,
                desc="Downloading data",
            )

            while True:
                time.sleep(0.5)
                downloaded_bytes = 0
                for directory in list_of_directories:
                    downloaded_bytes += IDCClient._get_dir_sum_file_size(directory)
                downloaded_bytes -= initial_size_bytes
                pbar.n = min(
                    downloaded_bytes, total_size_to_be_downloaded_bytes
                )  # Prevent the progress bar from exceeding 100%
                pbar.refresh()
                if process.poll() is not None:
                    break
            # Wait for the process to finish
            _, stderr = process.communicate()
            pbar.close()

        else:
            while process.poll() is None:
                time.sleep(0.5)

    @staticmethod
    def _get_dir_sum_file_size(directory) -> int:
        path = Path(directory)
        sum_file_size = 0
        if path.exists() and path.is_dir():
            for f in path.iterdir():
                if f.is_file():
                    try:
                        sum_file_size += f.stat().st_size
                    except FileNotFoundError:
                        # file must have been removed before we
                        # could get its size
                        pass
        return sum_file_size

    def _parse_s5cmd_sync_output_and_generate_synced_manifest(
        self, stdout, s5cmd_sync_helper_df
    ) -> Path:
        """
        Parse the output of s5cmd sync --dry-run to extract distinct folders and generate a synced manifest.

        Args:
            output (str): The output of s5cmd sync --dry-run command.
            s5cmd_sync_helper_df: helper df obtained after validation of manifest or filtering of selection, containing a minimum of "index_crdc_series_uuid", "s5cmd_cmd", "series_size_MB", "path" columns

        Returns:
            Path: The path to the generated synced manifest file.
            float: Download size in MB
            list_of_directories: list of directories need to tracked for progress bar
        """
        logger.info("Parsing the s5cmd sync dry run output...")

        stdout_df = pd.DataFrame(stdout.splitlines(), columns=["s5cmd_output"])

        # create a copy of the index
        index_df_copy = self.index

        result_df = s5cmd_sync_helper_df

        # TODO: need to remove the assumption that manifest commands will have 'cp'
        # ruff: noqa
        sql = """
            PRAGMA disable_progress_bar;
            WITH
            index_temp AS (
            SELECT
                 index_crdc_series_uuid,
                 s5cmd_cmd,
                 path,
                 series_size_MB
            FROM
                result_df),
            sync_temp AS (
            SELECT
                DISTINCT CONCAT(REGEXP_EXTRACT(s5cmd_output, 'cp (s3://[^/]+/[^/]+)/.*', 1), '/*') AS s3_url,
                REGEXP_EXTRACT(CONCAT(REGEXP_EXTRACT(s5cmd_output, 'cp (s3://[^/]+/[^/]+)/.*', 1), '/*'),'(?:.*?\\/){3}([^\\/?#]+)',1) AS sync_crdc_instance_uuid
            FROM
                stdout_df )
            SELECT
                DISTINCT s5cmd_cmd,
                series_size_MB,
                path
            FROM
                sync_temp
            JOIN
                index_temp
            ON
                index_temp.index_crdc_series_uuid = sync_temp.sync_crdc_instance_uuid
        """
        # ruff: noqa: end
        synced_df = duckdb.query(sql).df()
        sync_size = synced_df["series_size_MB"].sum()
        sync_size_rounded = round(sync_size, 2)

        logger.debug(f"sync_size_rounded: {sync_size_rounded}")

        # Write a temporary manifest file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as synced_manifest:
            list_of_directories = synced_df.path.to_list()
            commands = "\n".join(synced_df["s5cmd_cmd"])
            synced_manifest.write(commands)

            logger.info("Parsing the s5cmd sync dry run output finished")
        return Path(synced_manifest.name), sync_size_rounded, list_of_directories

    def _s5cmd_run(
        self,
        endpoint_to_use,
        manifest_file,
        total_size,
        downloadDir,
        quiet,
        show_progress_bar,
        use_s5cmd_sync,
        dirTemplate,
        list_of_directories,
        s5cmd_sync_helper_df,
    ):
        """
        Executes the s5cmd command to sync files from a given endpoint to a local directory.

        This function first performs a dry run of the s5cmd command to check which files need to be downloaded.
        If there are files to be downloaded, it generates a new manifest file with the files to be synced and
        runs the s5cmd command again to download the files. The progress of the download is tracked and printed
        to the console.

        Args:
            endpoint_to_use (str): The endpoint URL to download the files from.
            manifest_file (str): The path to the manifest file listing the files to be downloaded.
            total_size (float): The total size of the files to be downloaded in MB.
            downloadDir (str): The local directory where the files will be downloaded.
            quiet (bool): If True, suppresses the stdout and stderr of the s5cmd command.
            show_progress_bar (bool): If True, tracks the progress of download.
            use_s5cmd_sync (bool): If True, will use s5cmd sync operation instead of cp when downloadDirectory is not empty; this can significantly improve the download speed if the content is partially downloaded.
            dirTemplate (str): Download directory hierarchy template.
            list_of_directories(list): List of directories need to tracked for progress bar.
            s5cmd_sync_helper_df (df): helper df obtained after validation of manifest or filtering of selection, containing a minimum of "index_crdc_series_uuid", "s5cmd_cmd", "series_size_MB", "path" columns.

        Raises:
            subprocess.CalledProcessError: If the s5cmd command fails.

        Returns:
            None
        """
        logger.debug("running self._s5cmd_run. Inputs received:")
        logger.debug(f"endpoint_to_use: {endpoint_to_use}")
        logger.debug(f"manifest_file: {manifest_file}")
        logger.debug(f"total_size: {total_size}")
        logger.debug(f"downloadDir: {downloadDir}")
        logger.debug(f"quiet: {quiet}")
        logger.debug(f"show_progress_bar: {show_progress_bar}")
        logger.debug(f"use_s5cmd_sync: {use_s5cmd_sync}")
        logger.debug(f"dirTemplate: {dirTemplate}")

        if quiet:
            stdout = subprocess.DEVNULL
            stderr = subprocess.DEVNULL
        else:
            stdout = None
            stderr = None

        if use_s5cmd_sync and len(os.listdir(downloadDir)) != 0:
            logger.debug(
                "Requested progress bar along with s5cmd sync dry run.\
                        Using s5cmd sync dry run as the destination folder is not empty"
            )
            dry_run_cmd = [
                self.s5cmdPath,
                "--no-sign-request",
                "--dry-run",
                "--endpoint-url",
                endpoint_to_use,
                "run",
                manifest_file,
            ]

            process = subprocess.run(
                dry_run_cmd, stdout=subprocess.PIPE, text=True, check=False
            )

            if process.stdout:
                # Some files need to be downloaded
                logger.info(
                    """
stoud from s5cmd sync dry run is not empty. Parsing the output to
evaluate what to download and corresponding size with only series level precision
"""
                )
                (
                    synced_manifest,
                    sync_size,
                    list_of_directories,
                ) = self._parse_s5cmd_sync_output_and_generate_synced_manifest(
                    stdout=process.stdout,
                    s5cmd_sync_helper_df=s5cmd_sync_helper_df,
                )
                logger.info(f"sync_size (MB): {sync_size}")

                cmd = [
                    self.s5cmdPath,
                    "--no-sign-request",
                    "--endpoint-url",
                    endpoint_to_use,
                    "run",
                    synced_manifest,
                ]
                with subprocess.Popen(
                    cmd, stdout=stdout, stderr=stderr, universal_newlines=True
                ) as process:
                    if sync_size < total_size:
                        logger.info(
                            """
Destination folder is not empty and sync size is less than total size.
"""
                        )
                        existing_data_size = round(total_size - sync_size, 2)
                        logger.info(
                            f"Requested total download size is {total_size} MB, \
                                    however at least {existing_data_size} MB is already present,\
                                    so downloading only remaining up to {sync_size} MB\n\
                                    Please note that disk sizes are calculated at series level, \
                                    so if individual files are missing, displayed progress bar may\
                                    not be accurate."
                        )
                        self._track_download_progress(
                            sync_size,
                            downloadDir,
                            process,
                            show_progress_bar,
                            list_of_directories,
                        )
                    else:
                        self._track_download_progress(
                            total_size,
                            downloadDir,
                            process,
                            show_progress_bar,
                            list_of_directories,
                        )
            else:
                logger.info(
                    "It appears that all requested DICOM files are already present in destination folder"
                )
        else:
            logger.info(
                "Not using s5cmd sync as the destination folder is empty or sync or progress bar is not requested"
            )
            cmd = [
                self.s5cmdPath,
                "--no-sign-request",
                "--endpoint-url",
                endpoint_to_use,
                "run",
                manifest_file,
            ]

            # fedorov: did consider-using-with, and decided against it to keep the code more readable
            stderr_log_file = tempfile.NamedTemporaryFile(delete=False)  # pylint: disable=consider-using-with

            with subprocess.Popen(
                cmd,
                stdout=stdout,
                stderr=stderr_log_file,
                universal_newlines=True,
            ) as process:
                self._track_download_progress(
                    total_size,
                    downloadDir,
                    process,
                    show_progress_bar,
                    list_of_directories,
                )

                stderr_log_file.close()

                runtime_errors = []
                with open(stderr_log_file.name) as stderr_log_file:
                    for line in stderr_log_file.readlines():
                        if not quiet:
                            logger.info(line)
                        if line.startswith("ERROR"):
                            runtime_errors.append(line)

                Path(stderr_log_file.name).unlink()

                if len(runtime_errors) > 0:
                    logger.error(
                        "Download process failed with the following errors:\n"
                        + "\n".join(runtime_errors)
                    )

                # Check if download process completed successfully
                if process.returncode != 0:
                    logger.error(
                        f"Download process return non-zero exit code: {process.returncode}"
                    )
                else:
                    logger.info("Successfully downloaded files to %s", str(downloadDir))

    @staticmethod
    def _format_size(size, size_in_bytes: bool = False):
        if size_in_bytes:
            size_MB = size / (10**6)
        else:
            size_MB = size
        size_GB = size_MB / 1000
        size_TB = size_GB / 1000

        if size_TB >= 1:
            return f"{round(size_TB, 2)} TB"
        if size_GB >= 1:
            return f"{round(size_GB, 2)} GB"
        if size_MB >= 1:
            return f"{round(size_MB, 2)} MB"
        return f"{round(size, 2)} bytes"

    def download_from_manifest(
        self,
        manifestFile: str,
        downloadDir: str,
        quiet: bool = True,
        validate_manifest: bool = True,
        show_progress_bar: bool = True,
        use_s5cmd_sync: bool = False,
        dirTemplate=DOWNLOAD_HIERARCHY_DEFAULT,
    ) -> None:
        """
        Download the manifest file. In a series of steps, the manifest file
        is first validated to ensure every line contains a valid urls. It then
        gets the total size to be downloaded and runs download process on one
        process and download progress on another process.

        Args:
            manifestFile (str): The path to the manifest file.
            downloadDir (str): The directory to download the files to.
            quiet (bool): If True, suppresses the output of the subprocess. Defaults to True.
            validate_manifest (bool): If True, validates the manifest for any errors. Defaults to True.
            show_progress_bar (bool): If True, tracks the progress of download
            use_s5cmd_sync (bool): If True, will use s5cmd sync operation instead of cp when downloadDirectory is not empty; this can significantly improve the download speed if the content is partially downloaded
            dirTemplate (str): Download directory hierarchy template. This variable defines the folder hierarchy for the organizing the downloaded files in downloadDirectory. Defaults to index.DOWNLOAD_HIERARCHY_DEFAULT set to %collection_id/%PatientID/%StudyInstanceUID/%Modality_%SeriesInstanceUID. The template string can be built using a combination of selected metadata attributes (PatientID, collection_id, Modality, StudyInstanceUID, SeriesInstanceUID) that must be prefixed by '%'. The following special characters can be used as separators: '-' (hyphen), '/' (slash for subdirectories), '_' (underscore). When set to None all files will be downloaded to the download directory with no subdirectories.

        Raises:
            ValueError: If the download directory does not exist.
        """

        downloadDir = self._check_create_directory(downloadDir)

        # validate the manifest
        (
            total_size,
            endpoint_to_use,
            temp_manifest_file,
            list_of_directories,
            validation_result_df,
        ) = self._validate_update_manifest_and_get_download_size(
            manifestFile=manifestFile,
            downloadDir=downloadDir,
            validate_manifest=validate_manifest,
            use_s5cmd_sync=use_s5cmd_sync,
            dirTemplate=dirTemplate,
        )

        total_size_rounded = round(total_size, 2)
        logger.info("Total size: " + self._format_size(total_size_rounded))

        self._s5cmd_run(
            endpoint_to_use=endpoint_to_use,
            manifest_file=temp_manifest_file,
            total_size=total_size_rounded,
            downloadDir=downloadDir,
            quiet=quiet,
            show_progress_bar=show_progress_bar,
            use_s5cmd_sync=use_s5cmd_sync,
            dirTemplate=dirTemplate,
            list_of_directories=list_of_directories,
            s5cmd_sync_helper_df=validation_result_df,
        )

    def citations_from_manifest(
        self,
        manifestFile: str,
        citation_format: str = CITATION_FORMAT_APA,
    ):
        """Get the list of publications that should be cited/attributed for a cohort defined by a manifest.

        Args:
            manifestFile (str: string containing the path to the manifest file.
            format (str): string containing the format of the citation. Must be one of the following: CITATION_FORMAT_APA, CITATION_FORMAT_BIBTEX, CITATION_FORMAT_JSON. Defaults to CITATION_FORMAT_APA. Can be initialized to the alternative formats as allowed by DOI API, see https://citation.crosscite.org/docs.html#sec-4.

        Returns:
            List of citations in the requested format.
        """

        manifest_df = pd.read_csv(
            manifestFile,
            comment="#",
            skip_blank_lines=True,
            header=None,
            names=["manifest_line"],
        )
        uuid_pattern = r"s3://.*/([^/]+)/\*"
        manifest_df["crdc_series_uuid"] = manifest_df["manifest_line"].str.extract(
            uuid_pattern, expand=False
        )
        index_copy = self.index[["series_aws_url", "SeriesInstanceUID"]].copy()
        index_copy["crdc_series_uuid"] = index_copy["series_aws_url"].str.extract(
            uuid_pattern, expand=False
        )
        query = """
        SELECT
          SeriesInstanceUID
        FROM
          index_copy
        JOIN
          manifest_df
        ON
          index_copy.crdc_series_uuid = manifest_df.crdc_series_uuid
        """

        result_df = self.sql_query(query)

        return self.citations_from_selection(
            seriesInstanceUID=result_df["SeriesInstanceUID"].tolist(),
            citation_format=citation_format,
        )

    def citations_from_selection(
        self,
        collection_id=None,
        patientId=None,
        studyInstanceUID=None,
        seriesInstanceUID=None,
        citation_format=CITATION_FORMAT_APA,
    ):
        """Get the list of publications that should be cited/attributed for the specific collection, patient (case) ID, study or series UID.

        Args:
            collection_id: string or list of strings containing the values of collection_id to filter by
            patientId: string or list of strings containing the values of PatientID to filter by
            studyInstanceUID (str): string or list of strings containing the values of DICOM StudyInstanceUID to filter by
            seriesInstanceUID: string or list of strings containing the values of DICOM SeriesInstanceUID to filter by
            format: string containing the format of the citation. Must be one of the following: CITATION_FORMAT_APA, CITATION_FORMAT_BIBTEX, CITATION_FORMAT_JSON. Defaults to CITATION_FORMAT_APA. Can be initialized to the alternative formats as allowed by DOI API, see https://citation.crosscite.org/docs.html#sec-4.

        Returns:
            List of citations in the requested format.
        """

        result_df = self._safe_filter_by_selection(
            self.index,
            collection_id=collection_id,
            patientId=patientId,
            studyInstanceUID=studyInstanceUID,
            seriesInstanceUID=seriesInstanceUID,
            sopInstanceUID=None,
            crdc_series_uuid=None,
        )

        citations = []

        if not result_df.empty:
            distinct_dois = result_df["source_DOI"].unique().tolist()

            if len(distinct_dois) == 0:
                logger.error("No DOIs found for the selection.")
                return citations

            # include citation for the currently main IDC publication
            # https://doi.org/10.1148/rg.230180
            distinct_dois.append("10.1148/rg.230180")

            headers = {"accept": citation_format}
            timeout = 30

            for doi in distinct_dois:
                url = "https://dx.doi.org/" + doi

                logger.debug(f"Requesting citation for DOI: {doi}")

                response = requests.get(url, headers=headers, timeout=timeout)

                logger.debug("Received response: " + str(response.status_code))

                if response.status_code == 200:
                    if citation_format == self.CITATION_FORMAT_JSON:
                        citations.append(response.json())
                    else:
                        citations.append(response.text)
                    logger.debug("Received citation: " + citations[-1])

                else:
                    logger.error(f"Failed to get citation for DOI: {url}")
                    logger.error(
                        f"DOI server response status code: {response.status_code}"
                    )

        return citations

    def download_from_selection(
        self,
        downloadDir,
        dry_run=False,
        collection_id=None,
        patientId=None,
        studyInstanceUID=None,
        seriesInstanceUID=None,
        sopInstanceUID=None,
        crdc_series_uuid=None,
        quiet=True,
        show_progress_bar=True,
        use_s5cmd_sync=False,
        dirTemplate=DOWNLOAD_HIERARCHY_DEFAULT,
    ):
        """Download the files corresponding to the selection. The filtering will be applied in sequence (but does it matter?) by first selecting the collection(s), followed by
        patient(s), study(studies) and series. If no filtering is applied, all the files will be downloaded.

        Args:
            downloadDir: string containing the path to the directory to download the files to
            dry_run: calculates the size of the cohort but download does not start
            collection_id: string or list of strings containing the values of collection_id to filter by
            patientId: string or list of strings containing the values of PatientID to filter by
            studyInstanceUID: string or list of strings containing the values of DICOM StudyInstanceUID to filter by
            seriesInstanceUID: string or list of strings containing the values of DICOM SeriesInstanceUID to filter by
            sopInstanceUID: string or list of strings containing the values of DICOM SOPInstanceUID to filter by
            crdc_series_uuid: string or list of strings containing the values of crdc_series_uuid to filter by
            quiet (bool): If True, suppresses the output of the subprocess. Defaults to True
            show_progress_bar (bool): If True, tracks the progress of download
            use_s5cmd_sync (bool): If True, will use s5cmd sync operation instead of cp when downloadDirectory is not empty; this can significantly improve the download speed if the content is partially downloaded
            dirTemplate (str): Download directory hierarchy template. This variable defines the folder hierarchy for the organizing the downloaded files in downloadDirectory. Defaults to index.DOWNLOAD_HIERARCHY_DEFAULT set to %collection_id/%PatientID/%StudyInstanceUID/%Modality_%SeriesInstanceUID. The template string can be built using a combination of selected metadata attributes (PatientID, collection_id, Modality, StudyInstanceUID, SeriesInstanceUID) that must be prefixed by '%'. The following special characters can be used as separators: '-' (hyphen), '/' (slash for subdirectories), '_' (underscore). When set to None all files will be downloaded to the download directory with no subdirectories.

        """

        downloadDir = self._check_create_directory(downloadDir)

        # If SOPInstanceUID(s) are given, we need to join the main index with the instance-level index
        if sopInstanceUID:
            if hasattr(
                self, "sm_instance_index"
            ):  # check if instance-level index is installed
                download_df = self.sm_instance_index
            else:
                logger.error(
                    "Instance-level access not possible because instance-level index not installed."
                )
                raise ValueError(
                    "Instance-level access not possible because instance-level index not installed."
                )
            if use_s5cmd_sync:
                logger.warning(
                    "s5cmd sync is not supported for downloading individual files. Disabling sync."
                )
                use_s5cmd_sync = False
        elif crdc_series_uuid is not None:
            download_df = pd.concat(
                [
                    self.index[
                        [
                            "PatientID",
                            "collection_id",
                            "Modality",
                            "StudyInstanceUID",
                            "SeriesInstanceUID",
                            "crdc_series_uuid",
                            "series_aws_url",
                            "series_size_MB",
                        ]
                    ],
                    self.previous_versions_index[
                        [
                            "PatientID",
                            "collection_id",
                            "Modality",
                            "StudyInstanceUID",
                            "SeriesInstanceUID",
                            "crdc_series_uuid",
                            "series_aws_url",
                            "series_size_MB",
                        ]
                    ],
                ],
            )
        else:
            download_df = self.index

        result_df = self._safe_filter_by_selection(
            download_df,
            collection_id=collection_id,
            patientId=patientId,
            studyInstanceUID=studyInstanceUID,
            seriesInstanceUID=seriesInstanceUID,
            sopInstanceUID=sopInstanceUID,
            crdc_series_uuid=crdc_series_uuid,
        )

        if not sopInstanceUID:
            total_size = round(result_df["series_size_MB"].sum(), 2)
        else:
            total_size_bytes = round(result_df["instance_size"].sum(), 2)
            logger.info(
                "Total size of files to download: "
                + self._format_size(total_size_bytes, size_in_bytes=True)
            )
            total_size = total_size_bytes / (10**6)

        disk_free_space_MB = psutil.disk_usage(downloadDir).free / (1000 * 1000)
        if disk_free_space_MB < total_size:
            logger.error("Not enough free space on disk to download the files.")
            logger.error(
                "Total size of files to download: " + self._format_size(total_size)
            )
            logger.error(
                "Total free space on disk: " + self._format_size(disk_free_space_MB)
            )
            return

        logger.info(
            "Total free space on disk: "
            + str(psutil.disk_usage(downloadDir).free / (1000 * 1000 * 1000))
            + " GB"
        )

        if dry_run:
            logger.info(
                "Dry run. Not downloading files. Rerun with dry_run=False to download the files."
            )
            return

        if dirTemplate is not None:
            hierarchy = self._generate_sql_concat_for_building_directory(
                downloadDir=downloadDir,
                dirTemplate=dirTemplate,
            )
        else:
            hierarchy = f"CONCAT('{downloadDir}')"

        if sopInstanceUID:
            sql = f"""
                WITH temp as
                    (
                        SELECT
                            sopInstanceUID
                        FROM
                            result_df
                    )
                SELECT
                    series_aws_url,
                    CONCAT(TRIM('*' FROM series_aws_url), crdc_instance_uuid, '.dcm') as instance_aws_url,
                    REGEXP_EXTRACT(series_aws_url, '(?:.*?\\/){{3}}([^\\/?#]+)', 1) index_crdc_series_uuid,
                    {hierarchy} as path
                FROM
                    temp
                JOIN
                    sm_instance_index using (sopInstanceUID)
                LEFT JOIN
                    index using (seriesInstanceUID)
                """
        else:
            sql = f"""
                WITH temp as
                    (
                        SELECT
                            seriesInstanceUID
                        FROM
                            result_df
                    )
                SELECT
                    series_aws_url,
                    REGEXP_EXTRACT(series_aws_url, '(?:.*?\\/){{3}}([^\\/?#]+)', 1) index_crdc_series_uuid,
                    series_size_MB,
                    {hierarchy} as path
                FROM
                    temp
                JOIN
                    index using (seriesInstanceUID)
                """
        result_df = self.sql_query(sql)
        # Download the files and make temporary file to store the list of files to download

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as manifest_file:
            # Determine column containing the URL for instance / series-level access
            if sopInstanceUID:
                if not "instance_aws_url" in result_df:
                    result_df["instance_aws_url"] = (
                        result_df["series_aws_url"].replace("/*", "/")
                        + result_df["crdc_instance_uuid"]
                        + ".dcm"
                    )
                url_column = "instance_aws_url"
            else:
                url_column = "series_aws_url"

            if use_s5cmd_sync and len(os.listdir(downloadDir)) != 0:
                if dirTemplate is not None:
                    result_df["s5cmd_cmd"] = (
                        "sync " + result_df[url_column] + ' "' + result_df["path"] + '"'
                    )
                else:
                    result_df["s5cmd_cmd"] = (
                        "sync " + result_df[url_column] + ' "' + downloadDir + '"'
                    )
            elif dirTemplate is not None:
                result_df["s5cmd_cmd"] = (
                    "cp " + result_df[url_column] + ' "' + result_df["path"] + '"'
                )
            else:
                result_df["s5cmd_cmd"] = (
                    "cp " + result_df[url_column] + ' "' + downloadDir + '"'
                )

            # Combine all commands into a single string with newline separators
            commands = "\n".join(result_df["s5cmd_cmd"])
            manifest_file.write(commands)

            if dirTemplate is not None:
                list_of_directories = result_df.path.to_list()
            else:
                list_of_directories = [downloadDir]
        logger.debug(
            """
Temporary download manifest is generated and is passed to self._s5cmd_run
"""
        )
        if sopInstanceUID:
            s5cmd_sync_helper_df = None
        else:
            s5cmd_sync_helper_df = result_df[
                ["index_crdc_series_uuid", "s5cmd_cmd", "series_size_MB", "path"]
            ]
        self._s5cmd_run(
            endpoint_to_use=aws_endpoint_url,
            manifest_file=Path(manifest_file.name),
            total_size=total_size,
            downloadDir=downloadDir,
            quiet=quiet,
            show_progress_bar=show_progress_bar,
            use_s5cmd_sync=use_s5cmd_sync,
            dirTemplate=dirTemplate,
            list_of_directories=list_of_directories,
            s5cmd_sync_helper_df=s5cmd_sync_helper_df,
        )

    def download_dicom_instance(
        self,
        sopInstanceUID,
        downloadDir,
        dry_run=False,
        quiet=True,
        show_progress_bar=True,
        use_s5cmd_sync=False,
        dirTemplate=DOWNLOAD_HIERARCHY_DEFAULT,
    ) -> None:
        """
        Download the files corresponding to the seriesInstanceUID to the specified directory.

        Args:
            sopInstanceUID: string or list of strings containing the values of DICOM SOPInstanceUID to filter by
            downloadDir: string containing the path to the directory to download the files to
            dry_run: calculates the size of the cohort but download does not start
            quiet (bool): If True, suppresses the output of the subprocess. Defaults to True.
            show_progress_bar (bool): If True, tracks the progress of download
            use_s5cmd_sync (bool): If True, will use s5cmd sync operation instead of cp when downloadDirectory is not empty; this can significantly improve the download speed if the content is partially downloaded
            dirTemplate (str): Download directory hierarchy template. This variable defines the folder hierarchy for the organizing the downloaded files in downloadDirectory. Defaults to index.DOWNLOAD_HIERARCHY_DEFAULT set to %collection_id/%PatientID/%StudyInstanceUID/%Modality_%SeriesInstanceUID. The template string can be built using a combination of selected metadata attributes (PatientID, collection_id, Modality, StudyInstanceUID, SeriesInstanceUID) that must be prefixed by '%'. The following special characters can be used as separators: '-' (hyphen), '/' (slash for subdirectories), '_' (underscore). When set to None all files will be downloaded to the download directory with no subdirectories.

        Returns: None

        Raises:
            TypeError: If sopInstanceUID(s) passed is(are) not a string or list

        """
        self.download_from_selection(
            downloadDir,
            sopInstanceUID=sopInstanceUID,
            dry_run=dry_run,
            quiet=quiet,
            show_progress_bar=show_progress_bar,
            use_s5cmd_sync=use_s5cmd_sync,
            dirTemplate=dirTemplate,
        )

    def download_dicom_series(
        self,
        seriesInstanceUID,
        downloadDir,
        dry_run=False,
        quiet=True,
        show_progress_bar=True,
        use_s5cmd_sync=False,
        dirTemplate=DOWNLOAD_HIERARCHY_DEFAULT,
    ) -> None:
        """
        Download the files corresponding to the seriesInstanceUID to the specified directory.

        Args:
            seriesInstanceUID: string or list of strings containing the values of DICOM SeriesInstanceUID to filter by
            downloadDir: string containing the path to the directory to download the files to
            dry_run: calculates the size of the cohort but download does not start
            quiet (bool): If True, suppresses the output of the subprocess. Defaults to True.
            show_progress_bar (bool): If True, tracks the progress of download
            use_s5cmd_sync (bool): If True, will use s5cmd sync operation instead of cp when downloadDirectory is not empty; this can significantly improve the download speed if the content is partially downloaded
            dirTemplate (str): Download directory hierarchy template. This variable defines the folder hierarchy for the organizing the downloaded files in downloadDirectory. Defaults to index.DOWNLOAD_HIERARCHY_DEFAULT set to %collection_id/%PatientID/%StudyInstanceUID/%Modality_%SeriesInstanceUID. The template string can be built using a combination of selected metadata attributes (PatientID, collection_id, Modality, StudyInstanceUID, SeriesInstanceUID) that must be prefixed by '%'. The following special characters can be used as separators: '-' (hyphen), '/' (slash for subdirectories), '_' (underscore). When set to None all files will be downloaded to the download directory with no subdirectories.

        Returns: None

        Raises:
            TypeError: If seriesInstanceUID(s) passed is(are) not a string or list

        """
        self.download_from_selection(
            downloadDir,
            seriesInstanceUID=seriesInstanceUID,
            dry_run=dry_run,
            quiet=quiet,
            show_progress_bar=show_progress_bar,
            use_s5cmd_sync=use_s5cmd_sync,
            dirTemplate=dirTemplate,
        )

    def download_dicom_studies(
        self,
        studyInstanceUID,
        downloadDir,
        dry_run=False,
        quiet=True,
        show_progress_bar=True,
        use_s5cmd_sync=False,
        dirTemplate=DOWNLOAD_HIERARCHY_DEFAULT,
    ) -> None:
        """
        Download the files corresponding to the studyInstanceUID to the specified directory.

        Args:
            studyInstanceUID: string or list of strings containing the values of DICOM studyInstanceUID to filter by
            downloadDir: string containing the path to the directory to download the files to
            dry_run: calculates the size of the cohort but download does not start
            quiet (bool): If True, suppresses the output of the subprocess. Defaults to True.
            show_progress_bar (bool): If True, tracks the progress of download
            use_s5cmd_sync (bool): If True, will use s5cmd sync operation instead of cp when downloadDirectory is not empty; this can significantly improve the download speed if the content is partially downloaded
            dirTemplate (str): Download directory hierarchy template. This variable defines the folder hierarchy for the organizing the downloaded files in downloadDirectory. Defaults to index.DOWNLOAD_HIERARCHY_DEFAULT set to %collection_id/%PatientID/%StudyInstanceUID/%Modality_%SeriesInstanceUID. The template string can be built using a combination of selected metadata attributes (PatientID, collection_id, Modality, StudyInstanceUID, SeriesInstanceUID) that must be prefixed by '%'. The following special characters can be used as separators: '-' (hyphen), '/' (slash for subdirectories), '_' (underscore). When set to None all files will be downloaded to the download directory with no subdirectories.

        Returns: None

        Raises:
            TypeError: If seriesInstanceUID(s) passed is(are) not a string or list

        """
        self.download_from_selection(
            downloadDir,
            studyInstanceUID=studyInstanceUID,
            dry_run=dry_run,
            quiet=quiet,
            show_progress_bar=show_progress_bar,
            use_s5cmd_sync=use_s5cmd_sync,
            dirTemplate=dirTemplate,
        )

    def download_dicom_patients(
        self,
        patientId,
        downloadDir,
        dry_run=False,
        quiet=True,
        show_progress_bar=True,
        use_s5cmd_sync=False,
        dirTemplate=DOWNLOAD_HIERARCHY_DEFAULT,
    ) -> None:
        """
        Download the files corresponding to the studyInstanceUID to the specified directory.

        Args:
            patientId: string or list of strings containing the values of DICOM patientId to filter by
            downloadDir: string containing the path to the directory to download the files to
            dry_run: calculates the size of the cohort but download does not start
            quiet (bool): If True, suppresses the output of the subprocess. Defaults to True.
            show_progress_bar (bool): If True, tracks the progress of download
            use_s5cmd_sync (bool): If True, will use s5cmd sync operation instead of cp when downloadDirectory is not empty; this can significantly improve the download speed if the content is partially downloaded
            dirTemplate (str): Download directory hierarchy template. This variable defines the folder hierarchy for the organizing the downloaded files in downloadDirectory. Defaults to index.DOWNLOAD_HIERARCHY_DEFAULT set to %collection_id/%PatientID/%StudyInstanceUID/%Modality_%SeriesInstanceUID. The template string can be built using a combination of selected metadata attributes (PatientID, collection_id, Modality, StudyInstanceUID, SeriesInstanceUID) that must be prefixed by '%'. The following special characters can be used as separators: '-' (hyphen), '/' (slash for subdirectories), '_' (underscore). When set to None all files will be downloaded to the download directory with no subdirectories.

        Returns: None

        Raises:
            TypeError: If patientId(s) passed is(are) not a string or list

        """
        self.download_from_selection(
            downloadDir,
            patientId=patientId,
            dry_run=dry_run,
            quiet=quiet,
            show_progress_bar=show_progress_bar,
            use_s5cmd_sync=use_s5cmd_sync,
            dirTemplate=dirTemplate,
        )

    def download_collection(
        self,
        collection_id,
        downloadDir,
        dry_run=False,
        quiet=True,
        show_progress_bar=True,
        use_s5cmd_sync=False,
        dirTemplate=DOWNLOAD_HIERARCHY_DEFAULT,
    ) -> None:
        """
        Download the files corresponding to the studyInstanceUID to the specified directory.

        Args:
            collection_id: string or list of strings containing the values of DICOM patientId to filter by
            downloadDir: string containing the path to the directory to download the files to
            dry_run: calculates the size of the cohort but download does not start
            quiet (bool): If True, suppresses the output of the subprocess. Defaults to True.
            show_progress_bar (bool): If True, tracks the progress of download
            use_s5cmd_sync (bool): If True, will use s5cmd sync operation instead of cp when downloadDirectory is not empty; this can significantly improve the download speed if the content is partially downloaded
            dirTemplate (str): Download directory hierarchy template. This variable defines the folder hierarchy for the organizing the downloaded files in downloadDirectory. Defaults to index.DOWNLOAD_HIERARCHY_DEFAULT set to %collection_id/%PatientID/%StudyInstanceUID/%Modality_%SeriesInstanceUID. The template string can be built using a combination of selected metadata attributes (PatientID, collection_id, Modality, StudyInstanceUID, SeriesInstanceUID) that must be prefixed by '%'. The following special characters can be used as separators: '-' (hyphen), '/' (slash for subdirectories), '_' (underscore). When set to None all files will be downloaded to the download directory with no subdirectories.

        Returns: None

        Raises:
            TypeError: If collection_id(s) passed is(are) not a string or list

        """
        self.download_from_selection(
            downloadDir,
            collection_id=collection_id,
            dry_run=dry_run,
            quiet=quiet,
            show_progress_bar=show_progress_bar,
            use_s5cmd_sync=use_s5cmd_sync,
            dirTemplate=dirTemplate,
        )

    def sql_query(self, sql_query):
        """Execute SQL query against the table in the index using duckdb.

        Args:
            sql_query: string containing the SQL query to execute. The table name to use in the FROM clause is 'index' (without quotes).

        Returns:
            pandas dataframe containing the results of the query

        Raises:
            duckdb.Error: any exception that duckdb.query() raises
        """

        index = self.index

        logger.debug("Executing SQL query: " + sql_query)
        # TODO: find a more elegant way to automate the following:  https://www.perplexity.ai/search/write-python-code-that-iterate-XY9ppywbQFSRnOpgbwx_uQ
        if hasattr(self, "sm_index"):
            sm_index = self.sm_index
        if hasattr(self, "sm_instance_index"):
            sm_instance_index = self.sm_instance_index
        if hasattr(self, "clinical_index"):
            clinical_index = self.clinical_index
        return duckdb.query(sql_query).to_df()
