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
from packaging.version import Version
from tqdm import tqdm

logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.DEBUG)

aws_endpoint_url = "https://s3.amazonaws.com"
gcp_endpoint_url = "https://storage.googleapis.com"


class IDCClient:
    def __init__(self):
        file_path = idc_index_data.IDC_INDEX_PARQUET_FILEPATH

        # Read index file
        logger.debug(f"Reading index file v{idc_index_data.__version__}")
        self.index = pd.read_parquet(file_path)
        # self.index = self.index.astype(str).replace("nan", "")
        self.index["series_size_MB"] = self.index["series_size_MB"].astype(float)
        self.collection_summary = self.index.groupby("collection_id").agg(
            {"Modality": pd.Series.unique, "series_size_MB": "sum"}
        )

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
    def get_idc_version():
        """
        Returns the version of IDC data used in idc-index
        """
        idc_version = Version(idc_index_data.__version__).major
        return f"v{idc_version}"

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
            collection_id (str or a list of str): The collection id or list of collection ids. This should be in lower case separated by underscores.
                                For example, 'pdmr_texture_analysis'. or ['pdmr_texture_analysis','nlst']
            outputFormat (str, optional): The format in which to return the patient IDs. Available options are 'dict',
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
            patient_df = patient_df.rename(columns={"collection_id": "Collection"})
            patient_df = patient_df[["PatientID", "PatientSex", "PatientAge"]]
            patient_df = (
                patient_df.groupby("PatientID")
                .agg(
                    {
                        "PatientSex": lambda x: ",".join(x[x != ""].unique()),
                        "PatientAge": lambda x: ",".join(x[x != ""].unique()),
                    }
                )
                .reset_index()
            )

            patient_df = patient_df.drop_duplicates().sort_values(by="PatientID")
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
            outputFormat (str, optional): The format in which to return the studies. Available options are 'dict',
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
            studies_df["patient_study_size_MB"] = studies_df.groupby(
                ["PatientID", "StudyInstanceUID"]
            )["series_size_MB"].transform("sum")
            studies_df["patient_study_series_count"] = studies_df.groupby(
                ["PatientID", "StudyInstanceUID"]
            )["SeriesInstanceUID"].transform("count")
            studies_df["patient_study_instance_count"] = studies_df.groupby(
                ["PatientID", "StudyInstanceUID"]
            )["instanceCount"].transform("count")

            studies_df = studies_df.rename(
                columns={
                    "collection_id": "Collection",
                    "patient_study_series_count": "SeriesCount",
                }
            )

            # patient_study_df = patient_study_df[['PatientID', 'PatientSex', 'Collection', 'PatientAge', 'StudyInstanceUID', 'StudyDate', 'StudyDescription', 'patient_study_size_MB', 'SeriesCount', 'patient_study_instance_count']]
            studies_df = studies_df[
                ["StudyInstanceUID", "StudyDate", "StudyDescription", "SeriesCount"]
            ]
            # Group by 'StudyInstanceUID'
            studies_df = (
                studies_df.groupby("StudyInstanceUID")
                .agg(
                    {
                        "StudyDate": lambda x: ",".join(x[x != ""].unique()),
                        "StudyDescription": lambda x: ",".join(x[x != ""].unique()),
                        "SeriesCount": lambda x: int(x[x != ""].iloc[0])
                        if len(x[x != ""]) > 0
                        else 0,
                    }
                )
                .reset_index()
            )

            studies_df = studies_df.drop_duplicates().sort_values(
                by=["StudyDate", "StudyDescription", "SeriesCount"]
            )

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
            outputFormat (str, optional): The format in which to return the series. Available options are 'dict',
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
            string containing the IDC viewer URL for the given SeriesInstanceUID
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
                viewer_url = f"https://viewer.imaging.datacommons.cancer.gov/v3/viewer/?StudyInstanceUIDs={studyInstanceUID}&SeriesInstanceUID={seriesInstanceUID}"
        elif viewer_selector == "volview":
            # TODO! Not implemented yet
            pass
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
        show_progress_bar,
        use_s5cmd_sync_dry_run,
    ) -> tuple[float, str, Path]:
        """
        Validates the manifest file by checking the URLs in the manifest

        Args:
            manifestFile (str): The path to the manifest file.
            downloadDir (str): The path to the download directory.
            validate_manifest (bool, optional): If True, validates the manifest for any errors. Defaults to True.
            show_progress_bar (bool, optional): If True, tracks the progress of download
            use_s5cmd_sync_dry_run (bool, optional): If True, improves the accuracy of progress bar in unusual circumstances
        Returns:
            total_size (float): The total size of all series in the manifest file.
            endpoint_to_use (str): The endpoint URL to use (either AWS or GCP).
            temp_manifest_file(Path): Path to the temporary manifest file for downstream steps
        Raises:
            ValueError: If the manifest file does not exist, if any URL in the manifest file is invalid, or if any URL is inaccessible in both AWS and GCP.
            Exception: If the manifest contains URLs from both AWS and GCP.
        """
        logger.debug("manifest validation is requested: " + str(validate_manifest))

        print("Parsing the manifest. Please wait..")
        # Read the manifest as a csv file
        manifest_df = pd.read_csv(
            manifestFile, comment="#", skip_blank_lines=True, header=None
        )

        # Rename the column
        manifest_df.columns = ["manifest_cp_cmd"]

        # create a copy of the index
        index_df_copy = self.index

        # Extract s3 url and crdc_instance_uuid from the manifest copy commands
        # Next, extract crdc_instance_uuid from aws_series_url in the index and
        # try to verify if every series in the manifest is present in the index

        sql = """
            PRAGMA disable_progress_bar;
            with index_temp as
            (select
            seriesInstanceUID,
            series_aws_url,
            series_size_MB,
            regexp_extract(series_aws_url, '(?:.*?\\/){3}([^\\/?#]+)', 1) index_crdc_series_uuid
            from index_df_copy),
            manifest_temp as (
            select
            manifest_cp_cmd,
            regexp_extract(manifest_cp_cmd, '(?:.*?\\/){3}([^\\/?#]+)', 1) as manifest_crdc_series_uuid,
            regexp_replace(regexp_replace(manifest_cp_cmd, 'cp ', ''), '\\s[^\\s]*$', '') as s3_url,
            from
            manifest_df
            )
            select
            seriesInstanceuid,
            s3_url,
            series_size_MB,
            index_crdc_series_uuid==manifest_crdc_series_uuid as crdc_series_uuid_match,
            s3_url==series_aws_url as s3_url_match,
            CASE WHEN s3_url==series_aws_url THEN 'aws' ELSE 'unknown' END as endpoint
            from
            manifest_temp
            left join index_temp on index_temp.index_crdc_series_uuid = manifest_temp.manifest_crdc_series_uuid
            """
        merged_df = duckdb.query(sql).df()

        if validate_manifest:
            # Check if crdc_instance_uuid is found in the index
            if not all(merged_df["crdc_series_uuid_match"]):
                missing_manifest_cp_cmds = merged_df.loc[
                    ~merged_df["crdc_series_uuid_match"], "manifest_cp_cmd"
                ]
                missing_manifest_cp_cmds_str = f"The following manifest copy commands do not have any associated series in the index: {missing_manifest_cp_cmds.tolist()}"
                raise ValueError(missing_manifest_cp_cmds_str)

            # Check if there are more than one endpoints
            if len(merged_df["endpoint"].unique()) > 1:
                raise ValueError(
                    "Either GCS bucket path is invalid or manifest has a mix of GCS and AWS urls. If so, please use urls from one provider only"
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
            endpoint_to_use = gcp_endpoint_url

        # Calculate total size
        total_size = merged_df["series_size_MB"].sum()
        total_size = round(total_size, 2)

        # Write a temporary manifest file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_manifest_file:
            if (
                show_progress_bar
                and use_s5cmd_sync_dry_run
                and len(os.listdir(downloadDir)) != 0
            ):
                merged_df["s5cmd_cmd"] = (
                    "sync " + merged_df["s3_url"] + " " + downloadDir
                )
            else:
                merged_df["s5cmd_cmd"] = "cp " + merged_df["s3_url"] + " " + downloadDir
            merged_df["s5cmd_cmd"].to_csv(temp_manifest_file, header=False, index=False)
            print("Parsing the manifest is finished. Download will begin soon")
        return total_size, endpoint_to_use, Path(temp_manifest_file.name)

    @staticmethod
    def _track_download_progress(
        size_MB: int,
        downloadDir: str,
        process: subprocess.Popen,
        show_progress_bar: bool = True,
    ):
        logger.info("Inputs received for tracking download:")
        logger.info(f"size_MB: {size_MB}")
        logger.info(f"downloadDir: {downloadDir}")
        logger.info(f"show_progress_bar: {show_progress_bar}")

        if show_progress_bar:
            total_size_bytes = size_MB * 10**6  # Convert MB to bytes

            # Calculate the initial size of the directory
            initial_size_bytes = sum(
                f.stat().st_size for f in Path(downloadDir).iterdir() if f.is_file()
            )

            logger.info("Initial size of the directory: %s bytes", initial_size_bytes)
            logger.info(
                "Approx. Size of the files need to be downloaded: %s bytes",
                total_size_bytes,
            )

            pbar = tqdm(
                total=total_size_bytes,
                unit="B",
                unit_scale=True,
                desc="Downloading data",
            )

            while True:
                downloaded_bytes = (
                    sum(
                        f.stat().st_size
                        for f in Path(downloadDir).iterdir()
                        if f.is_file()
                    )
                    - initial_size_bytes
                )
                pbar.n = min(
                    downloaded_bytes, total_size_bytes
                )  # Prevent the progress bar from exceeding 100%
                pbar.refresh()

                if process.poll() is not None:
                    break

                time.sleep(0.5)

            # Wait for the process to finish
            stdout, stderr = process.communicate()
            pbar.close()

        else:
            while process.poll() is None:
                time.sleep(0.5)

        # Check if download process completed successfully
        if process.returncode != 0:
            error_message = f"Download process failed: {stderr!s}"
            logger.error(error_message)
            raise RuntimeError(error_message)

        logger.info("Successfully downloaded files to %s", str(downloadDir))

    def _parse_s5cmd_sync_output_and_generate_synced_manifest(
        self, stdout, downloadDir
    ) -> Path:
        """
        Parse the output of s5cmd sync --dry-run to extract distinct folders and generate a synced manifest.

        Args:
            output (str): The output of s5cmd sync --dry-run command.
            downloadDir (str): The directory to download the files to.

        Returns:
            Path: The path to the generated synced manifest file.
            float: Download size in MB
        """
        logger.info("Parsing the s5cmd sync dry run output...")

        stdout_df = pd.DataFrame(stdout.splitlines(), columns=["s5cmd_output"])

        # create a copy of the index
        index_df_copy = self.index

        sql = """
            PRAGMA disable_progress_bar;
            with index_temp as
            (select
            *,
            regexp_extract(series_aws_url, '(?:.*?\\/){3}([^\\/?#]+)', 1) index_crdc_series_uuid
            from index_df_copy),
            sync_temp as (
            select
            distinct
            concat(regexp_extract(s5cmd_output, 'cp (s3://[^/]+/[^/]+)/.*', 1), '/*') as s3_url,
            regexp_extract(concat(regexp_extract(s5cmd_output, 'cp (s3://[^/]+/[^/]+)/.*', 1), '/*'),'(?:.*?\\/){3}([^\\/?#]+)',1) as sync_crdc_instance_uuid
            from
            stdout_df
            )
            select
            distinct
            seriesInstanceUID,
            series_size_MB,
            s3_url
            from
            sync_temp
            left join index_temp on index_temp.index_crdc_series_uuid = sync_temp.sync_crdc_instance_uuid
        """
        merged_df = duckdb.query(sql).df()
        sync_size = merged_df["series_size_MB"].sum()
        sync_size_rounded = round(sync_size, 2)

        logger.info(f"sync_size_rounded: {sync_size_rounded}")

        # Write a temporary manifest file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as synced_manifest:
            merged_df["s5cmd_cmd"] = "sync " + merged_df["s3_url"] + " " + downloadDir
            merged_df["s5cmd_cmd"].to_csv(synced_manifest, header=False, index=False)
            logger.info("Parsing the s5cmd sync dry run output finished")
        return Path(synced_manifest.name), sync_size_rounded

    def _s5cmd_run(
        self,
        endpoint_to_use,
        manifest_file,
        total_size,
        downloadDir,
        quiet,
        show_progress_bar,
        use_s5cmd_sync_dry_run,
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
            quiet (bool, optional): If True, suppresses the stdout and stderr of the s5cmd command.
            show_progress_bar (bool, optional): If True, tracks the progress of download
            use_s5cmd_sync_dry_run (bool, optional): If True, improves the accuracy of progress bar in unusual circumstances

        Raises:
            subprocess.CalledProcessError: If the s5cmd command fails.

        Returns:
            None
        """
        logger.info("running self._s5cmd_run. Inputs received:")
        logger.info(f"endpoint_to_use: {endpoint_to_use}")
        logger.info(f"manifest_file: {manifest_file}")
        logger.info(f"total_size: {total_size}")
        logger.info(f"downloadDir: {downloadDir}")
        logger.info(f"quiet: {quiet}")
        logger.info(f"show_progress_bar: {show_progress_bar}")
        logger.info(f"use_s5cmd_sync_dry_run: {use_s5cmd_sync_dry_run}")

        if quiet:
            stdout = subprocess.DEVNULL
            stderr = subprocess.DEVNULL
        else:
            stdout = None
            stderr = None

        if (
            show_progress_bar
            and use_s5cmd_sync_dry_run
            and len(os.listdir(downloadDir)) != 0
        ):
            logger.info(
                """
Requested progress bar along with s5cmd sync dry run.
Using s5cmd sync dry run as the destination folder is not empty
"""
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
                ) = self._parse_s5cmd_sync_output_and_generate_synced_manifest(
                    stdout=process.stdout, downloadDir=downloadDir
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
Destination folder is not empty and sync size is less than total size. Displaying a warning
"""
                        )
                        existing_data_size = round(total_size - sync_size, 2)
                        print(
                            f"""
Requested total download size is {total_size} MB, however at least {existing_data_size} MB is already present,
so downloading only remaining upto {sync_size} MB

Please note that disk sizes are calculated at series level, so if individual files are missing,
displayed progress bar may not be accurate.
"""
                        )
                        self._track_download_progress(
                            sync_size, downloadDir, process, show_progress_bar
                        )
                    else:
                        self._track_download_progress(
                            total_size, downloadDir, process, show_progress_bar
                        )
            else:
                logger.info(
                    """
stoud from s5cmd sync dry run is empty, indicating all requested DICOM files are already present in destination folder
"""
                )
                # All requested DICOM files are already present
                print(
                    f"All requested DICOM files are already present in {downloadDir}."
                )
        else:
            logger.info(
                """
NOT using s5cmd sync dry run as the destination folder IS empty or sync dry or progress bar is not requested
"""
            )
            cmd = [
                self.s5cmdPath,
                "--no-sign-request",
                "--endpoint-url",
                endpoint_to_use,
                "run",
                manifest_file,
            ]
            with subprocess.Popen(
                cmd, stdout=stdout, stderr=stderr, universal_newlines=True
            ) as process:
                self._track_download_progress(
                    total_size, downloadDir, process, show_progress_bar
                )

    @staticmethod
    def _format_size(size_MB):
        size_GB = size_MB / 1000
        size_TB = size_GB / 1000

        if size_TB >= 1:
            return f"{round(size_TB, 2)} TB"
        if size_GB >= 1:
            return f"{round(size_GB, 2)} GB"
        return f"{round(size_MB, 2)} MB"

    def download_from_manifest(
        self,
        manifestFile: str,
        downloadDir: str,
        quiet: bool = True,
        validate_manifest: bool = True,
        show_progress_bar: bool = True,
        use_s5cmd_sync_dry_run: bool = False,
    ) -> None:
        """
        Download the manifest file. In a series of steps, the manifest file
        is first validated to ensure every line contains a valid urls. It then
        gets the total size to be downloaded and runs download process on one
        process and download progress on another process.

        Args:
            manifestFile (str): The path to the manifest file.
            downloadDir (str): The directory to download the files to.
            quiet (bool, optional): If True, suppresses the output of the subprocess. Defaults to True.
            validate_manifest (bool, optional): If True, validates the manifest for any errors. Defaults to True.
            show_progress_bar (bool, optional): If True, tracks the progress of download
            use_s5cmd_sync_dry_run (bool, optional): If True, improves the accuracy of progress bar in unusual circumstances

        Raises:
            ValueError: If the download directory does not exist.
        """

        downloadDir = os.path.abspath(downloadDir).replace("\\", "/")
        if not os.path.exists(downloadDir):
            raise ValueError("Download directory does not exist.")

        # validate the manifest
        (
            total_size,
            endpoint_to_use,
            temp_manifest_file,
        ) = self._validate_update_manifest_and_get_download_size(
            manifestFile,
            downloadDir,
            validate_manifest,
            show_progress_bar,
            use_s5cmd_sync_dry_run,
        )

        total_size_rounded = round(total_size, 2)
        print("Total size: " + self._format_size(total_size_rounded))

        self._s5cmd_run(
            endpoint_to_use=endpoint_to_use,
            manifest_file=temp_manifest_file,
            total_size=total_size_rounded,
            downloadDir=downloadDir,
            quiet=quiet,
            show_progress_bar=show_progress_bar,
            use_s5cmd_sync_dry_run=use_s5cmd_sync_dry_run,
        )

    def download_from_selection(
        self,
        downloadDir,
        dry_run=False,
        collection_id=None,
        patientId=None,
        studyInstanceUID=None,
        seriesInstanceUID=None,
        quiet=True,
        show_progress_bar=True,
        use_s5cmd_sync_dry_run=False,
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
            quiet (bool, optional): If True, suppresses the output of the subprocess. Defaults to True.
            show_progress_bar (bool, optional): If True, tracks the progress of download
            use_s5cmd_sync_dry_run (bool, optional): If True, improves the accuracy of progress bar in unusual circumstances

        Returns:

        Raises:
            TypeError: If any of the parameters are not of the expected type
        """

        downloadDir = os.path.abspath(downloadDir).replace("\\", "/")
        if not os.path.exists(downloadDir):
            raise ValueError("Download directory does not exist.")

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

        if collection_id is not None:
            result_df = self._filter_by_collection_id(self.index, collection_id)
        else:
            result_df = self.index

        if patientId is not None:
            result_df = self._filter_by_patient_id(result_df, patientId)

        if studyInstanceUID is not None:
            result_df = self._filter_by_dicom_study_uid(result_df, studyInstanceUID)

        if seriesInstanceUID is not None:
            result_df = self._filter_by_dicom_series_uid(result_df, seriesInstanceUID)

        total_size = round(result_df["series_size_MB"].sum(), 2)
        logger.info(
            "Total size of files to download: " + str(float(total_size) / 1000) + "GB"
        )
        logger.info(
            "Total free space on disk: "
            + str(psutil.disk_usage(downloadDir).free / (1024 * 1024 * 1024))
            + "GB"
        )

        if dry_run:
            logger.info(
                "Dry run. Not downloading files. Rerun with dry_run=False to download the files."
            )
        else:
            print("Total size: " + self._format_size(total_size))
            # Download the files
            # make temporary file to store the list of files to download
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as manifest_file:
                if (
                    show_progress_bar
                    and use_s5cmd_sync_dry_run
                    and len(os.listdir(downloadDir)) != 0
                ):
                    result_df["s5cmd_cmd"] = (
                        "sync " + result_df["series_aws_url"] + " " + downloadDir
                    )
                else:
                    result_df["s5cmd_cmd"] = (
                        "cp " + result_df["series_aws_url"] + " " + downloadDir
                    )
                result_df["s5cmd_cmd"].to_csv(manifest_file, header=False, index=False)
            logger.info(
                """
Temporary download manifest is generated and is passed to self._s5cmd_run
"""
            )
            self._s5cmd_run(
                endpoint_to_use=aws_endpoint_url,
                manifest_file=Path(manifest_file.name),
                total_size=total_size,
                downloadDir=downloadDir,
                quiet=quiet,
                show_progress_bar=show_progress_bar,
                use_s5cmd_sync_dry_run=use_s5cmd_sync_dry_run,
            )

    def download_dicom_series(
        self,
        seriesInstanceUID,
        downloadDir,
        dry_run=False,
        quiet=True,
        show_progress_bar=True,
        use_s5cmd_sync_dry_run=False,
    ) -> None:
        """
        Download the files corresponding to the seriesInstanceUID to the specified directory.

        Args:
            seriesInstanceUID: string or list of strings containing the values of DICOM SeriesInstanceUID to filter by
            downloadDir: string containing the path to the directory to download the files to
            dry_run: calculates the size of the cohort but download does not start
            quiet (bool, optional): If True, suppresses the output of the subprocess. Defaults to True.
            show_progress_bar (bool, optional): If True, tracks the progress of download
            use_s5cmd_sync_dry_run (bool, optional): If True, improves the accuracy of progress bar in unusual circumstances

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
            use_s5cmd_sync_dry_run=use_s5cmd_sync_dry_run,
        )

    def download_dicom_studies(
        self,
        studyInstanceUID,
        downloadDir,
        dry_run=False,
        quiet=True,
        show_progress_bar=True,
        use_s5cmd_sync_dry_run=False,
    ) -> None:
        """
        Download the files corresponding to the studyInstanceUID to the specified directory.

        Args:
            studyInstanceUID: string or list of strings containing the values of DICOM studyInstanceUID to filter by
            downloadDir: string containing the path to the directory to download the files to
            dry_run: calculates the size of the cohort but download does not start
            quiet (bool, optional): If True, suppresses the output of the subprocess. Defaults to True.
            show_progress_bar (bool, optional): If True, tracks the progress of download
            use_s5cmd_sync_dry_run (bool, optional): If True, improves the accuracy of progress bar in unusual circumstances

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
            use_s5cmd_sync_dry_run=use_s5cmd_sync_dry_run,
        )

    def download_dicom_patients(
        self,
        patientId,
        downloadDir,
        dry_run=False,
        quiet=True,
        show_progress_bar=True,
        use_s5cmd_sync_dry_run=False,
    ) -> None:
        """
        Download the files corresponding to the studyInstanceUID to the specified directory.

        Args:
            patientId: string or list of strings containing the values of DICOM patientId to filter by
            downloadDir: string containing the path to the directory to download the files to
            dry_run: calculates the size of the cohort but download does not start
            quiet (bool, optional): If True, suppresses the output of the subprocess. Defaults to True.
            show_progress_bar (bool, optional): If True, tracks the progress of download
            use_s5cmd_sync_dry_run (bool, optional): If True, improves the accuracy of progress bar in unusual circumstances

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
            use_s5cmd_sync_dry_run=use_s5cmd_sync_dry_run,
        )

    def download_collection(
        self,
        collection_id,
        downloadDir,
        dry_run=False,
        quiet=True,
        show_progress_bar=True,
        use_s5cmd_sync_dry_run=False,
    ) -> None:
        """
        Download the files corresponding to the studyInstanceUID to the specified directory.

        Args:
            collection_id: string or list of strings containing the values of DICOM patientId to filter by
            downloadDir: string containing the path to the directory to download the files to
            dry_run: calculates the size of the cohort but download does not start
            quiet (bool, optional): If True, suppresses the output of the subprocess. Defaults to True.
            show_progress_bar (bool, optional): If True, tracks the progress of download
            use_s5cmd_sync_dry_run (bool, optional): If True, improves the accuracy of progress bar in unusual circumstances

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
            use_s5cmd_sync_dry_run=use_s5cmd_sync_dry_run,
        )

    def sql_query(self, sql_query):
        """Execute SQL query against the table in the index using duckdb.

        Args:
            sql_query: string containing the SQL query to execute. The table name to use in the FROM clause is 'index' (without quotes).

        Returns:
            pandas dataframe containing the results of the query

        Raises:
            any exception that duckdb.query() raises
        """

        index = self.index
        return duckdb.query(sql_query).to_df()
