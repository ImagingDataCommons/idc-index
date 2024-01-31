import os
import logging
import pandas as pd
import platform
import subprocess
import duckdb
import urllib.request
import re
import tempfile

logger = logging.getLogger(__name__)

idc_version = "v17"
release_version = "0.2.11"
aws_endpoint_url = "https://s3.amazonaws.com"
gcp_endpoint_url = "https://storage.googleapis.com"
latest_idc_index_csv_url = 'https://github.com/ImagingDataCommons/idc-index/releases/download/'+release_version+'/idc_index.csv.zip'

class IDCClient:
    def __init__(self):


        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'idc_index.csv.zip')
        if not os.path.exists(file_path):
            logger.warning("Index file not found. Downloading latest version of the index file. This will take a minute or so.")
            urllib.request.urlretrieve(latest_idc_index_csv_url, file_path)
            logger.warning("Index file downloaded.")
        self.index = pd.read_csv(file_path, dtype=str, encoding='utf-8')
        self.index = self.index.astype(str).replace('nan', '')
        self.index['series_size_MB'] = self.index['series_size_MB'].astype(float)
        self.collection_summary = self.index.groupby('collection_id').agg({
            'Modality': pd.Series.unique,
            'series_size_MB': 'sum'
        })
        
        self.s5cmdPath = None 
        system = platform.system()

        if system == "Windows":
            self.s5cmdPath = os.path.join(current_dir, 's5cmd.exe')
        elif system == "Darwin":
            self.s5cmdPath = os.path.join(current_dir, 's5cmd')
        else:
            self.s5cmdPath = os.path.join(current_dir, 's5cmd')

        if not os.path.exists(self.s5cmdPath):
            # try to check if there is a s5cmd executable in the path
            try:
                subprocess.run(['s5cmd', '--help'], capture_output=False, text=False)
                self.s5cmdPath = 's5cmd'
            except:
                logger.fatal("s5cmd executable not found. Please install s5cmd from https://github.com/peak/s5cmd#installation")
                raise ValueError

        # Print after successful reading of index
        logger.debug("Successfully read the index and located s5cmd.")


    def _filter_by_collection_id(self, df, collection_id):
        if isinstance(collection_id, str):
            result_df = df[df['collection_id'].isin([collection_id])].copy()
        else:
            result_df = df[df['collection_id'].isin(collection_id)].copy()
        return result_df

    def _filter_by_patient_id(self, df, patient_id):
        if isinstance(patient_id, str):
            result_df = df[df['PatientID'].isin([patient_id])].copy()
        else:
            result_df = df[df['PatientID'].isin(patient_id)].copy()
        return result_df

    def _filter_by_dicom_study_uid(self, df, dicom_study_uid):
        if isinstance(dicom_study_uid, str):
            result_df = df[df['StudyInstanceUID'].isin([dicom_study_uid])].copy()
        else:
            result_df = df[df['StudyInstanceUID'].isin(dicom_study_uid)].copy()
        return result_df

    def _filter_by_dicom_series_uid(self, df, dicom_series_uid):
        if isinstance(dicom_series_uid, str):
            result_df = df[df['SeriesInstanceUID'].isin([dicom_series_uid])].copy()
        else:
            result_df = df[df['SeriesInstanceUID'].isin(dicom_series_uid)].copy()
        return result_df

    def get_idc_version(self):
        return idc_version;
    
    def get_collections(self):
        unique_collections = self.index['collection_id'].unique()
        return unique_collections.tolist()
    
    def get_series_size(self, seriesInstanceUID):
        resp = self.index[['SeriesInstanceUID']==seriesInstanceUID]['series_size_MB'].iloc[0]
        return resp

    def get_patients(self, collection_id, outputFormat="dict"):
        if not isinstance(collection_id, str) and not isinstance(collection_id, list):
            raise TypeError("collection_id must be a string or list of strings")

        if not outputFormat in ["dict","df","list"]:
            raise ValueError("outputFormat must be either 'dict', 'df', or 'list")

        patient_df = self._filter_by_collection_id(self.index, collection_id)

        if outputFormat == "list":
            response = patient_df['PatientID'].unique().tolist()
        else:
            patient_df=patient_df.rename(columns={'collection_id':'Collection'})
            patient_df = patient_df[['PatientID', 'PatientSex', 'PatientAge']]
            patient_df = patient_df.groupby('PatientID').agg({
                'PatientSex': lambda x: ','.join(x[x != ''].unique()),
                'PatientAge': lambda x: ','.join(x[x != ''].unique())
            }).reset_index()

            patient_df = patient_df.drop_duplicates().sort_values(by='PatientID')
            # Convert DataFrame to a list of dictionaries for the API-like response
            if outputFormat == "dict":
                response = patient_df.to_dict(orient="records")
            else:
                response = patient_df

        logger.debug("Get patient response: %s", str(response))

        return response

    
    def get_dicom_studies(self, patientId, outputFormat="dict"):
        """returns one row per distinct value of StudyInstanceUID
        """

        if not isinstance(patientId, str) and not isinstance(patientId, list):
            raise TypeError("patientId must be a string or list of strings")
        
        if not outputFormat in ["dict","df","list"]:
            raise ValueError("outputFormat must be either 'dict' or 'df' or 'list'")

        studies_df = self._filter_by_patient_id(self.index, patientId) 


        if outputFormat == "list":
            response = studies_df['StudyInstanceUID'].unique().tolist()
        else:   
            studies_df['patient_study_size_MB'] = studies_df.groupby(['PatientID', 'StudyInstanceUID'])['series_size_MB'].transform('sum')
            studies_df['patient_study_series_count'] = studies_df.groupby(['PatientID', 'StudyInstanceUID'])['SeriesInstanceUID'].transform('count')
            studies_df['patient_study_instance_count'] = studies_df.groupby(['PatientID', 'StudyInstanceUID'])['instanceCount'].transform('count')

            studies_df = studies_df.rename(columns={'collection_id': 'Collection', 'patient_study_series_count': 'SeriesCount'})

            #patient_study_df = patient_study_df[['PatientID', 'PatientSex', 'Collection', 'PatientAge', 'StudyInstanceUID', 'StudyDate', 'StudyDescription', 'patient_study_size_MB', 'SeriesCount', 'patient_study_instance_count']]
            studies_df = studies_df[['StudyInstanceUID', 'StudyDate', 'StudyDescription', 'SeriesCount']]
            # Group by 'StudyInstanceUID'
            studies_df = studies_df.groupby('StudyInstanceUID').agg({
                'StudyDate': lambda x: ','.join(x[x != ''].unique()),
                'StudyDescription': lambda x: ','.join(x[x != ''].unique()),
                'SeriesCount': lambda x: int(x[x != ''].iloc[0]) if len(x[x != '']) > 0 else 0
            }).reset_index()

            studies_df = studies_df.drop_duplicates().sort_values(by=['StudyDate','StudyDescription','SeriesCount'])


            if outputFormat == "dict":
                response = studies_df.to_dict(orient="records")
            else:
                response = studies_df
                
        logger.debug("Get patient study response: %s", str(response))

        return response

    def get_dicom_series(self, studyInstanceUID=None,outputFormat="dict"):
        if not isinstance(studyInstanceUID, str) and not isinstance(studyInstanceUID, list):
            raise TypeError("studyInstanceUID must be a string or list of strings")
        
        if not outputFormat in ["dict","df","list"]:
            raise ValueError("outputFormat must be either 'dict' or 'df' or 'list'")

        series_df = self._filter_by_dicom_study_uid(self.index, studyInstanceUID) 
       
        if outputFormat == "list":
            response = series_df['SeriesInstanceUID'].unique().tolist()
        else:
            series_df = series_df.rename(columns={'collection_id': 'Collection', 'instanceCount': 'instance_count'})
            series_df['ImageCount']=1
            series_df = series_df[['StudyInstanceUID', 'SeriesInstanceUID', 'Modality', 'SeriesDate', 'Collection', 'BodyPartExamined', 'SeriesDescription', 'Manufacturer', 'ManufacturerModelName', 'series_size_MB','SeriesNumber', 'instance_count', 'ImageCount']]

            series_df = series_df.drop_duplicates().sort_values(by=['Modality','SeriesDate','SeriesDescription','BodyPartExamined', 'SeriesNumber'])
            # Convert DataFrame to a list of dictionaries for the API-like response
            if outputFormat == "dict":
                response = series_df.to_dict(orient="records")
            else:
                response = series_df
        logger.debug("Get series response: %s", str(response))

        return response

    def download_dicom_series(self, seriesInstanceUID, downloadDir, dry_run=False, quiet=True):
        """
        Download the files corresponding to the seriesInstanceUID to the specified directory.

        Args:
            seriesInstanceUID: string containing the value of DICOM SeriesInstanceUID to filter by
            downloadDir: string containing the path to the directory to download the files to
            dry_run: boolean indicating if the download should be a dry run (default: False)
            quiet: boolean indicating if the output should be suppressed (default: True)
        
        Returns:

        """
        series_url = self.index[self.index['SeriesInstanceUID'] == seriesInstanceUID]['series_aws_url'].iloc[0]
        logger.debug('AWS Bucket Location: '+series_url)

        cmd = [self.s5cmdPath, '--no-sign-request', '--endpoint-url', aws_endpoint_url, 'cp', '--show-progress',
            series_url, downloadDir]

        if not dry_run:
            process = subprocess.run(cmd, capture_output=(not quiet), text=(not quiet))
            if not quiet:
                print(process.stderr)
            if process.returncode == 0:
                logger.debug(f"Successfully downloaded files to {downloadDir}")
            else:
                logger.error("Failed to download files.")

    def get_series_file_URLs(self, seriesInstanceUID):
        """
        Get the URLs of the files corresponding to the DICOM instances in a given SeriesInstanceUID.

        Args:
            SeriesInstanceUID: string containing the value of DICOM SeriesInstanceUID to filter by

        Returns:
            list of strings containing the AWS S3 URLs of the files corresponding to the SeriesInstanceUID
        """
        # Query to get the S3 URL
        s3url_query = f'''
        SELECT
          series_aws_url
        FROM
          index
        WHERE
          SeriesInstanceUID='{seriesInstanceUID}'
        '''
        s3url_query_df = self.sql_query(s3url_query)
        s3_url = s3url_query_df.series_aws_url[0]

        # Remove the last character from the S3 URL
        s3_url = s3_url[:-1]

        # Run the s5cmd ls command and capture its output
        result = subprocess.run([self.s5cmdPath, '--no-sign-request', 'ls', s3_url], stdout=subprocess.PIPE)
        output = result.stdout.decode('utf-8')

        # Parse the output to get the file names
        lines = output.split('\n')
        file_names = [s3_url+line.split()[-1] for line in lines if line]

        return file_names

    def get_viewer_URL(self, seriesInstanceUID, studyInstanceUID=None, viewer_selector=None):
        """
        Get the URL of the IDC viewer for the given series or study in IDC based on
        the provided SeriesInstanceUID or StudyInstanceUID. If StudyInstanceUID is not provided,
        it will be automatically deduced. If viewer_selector is not provided, default viewers
        will be used (OHIF v2 for radiology modalities, and Slim for SM).

        This function will validate the provided SeriesInstanceUID or StudyInstanceUID against IDC
        index to ensure that the series or study is available in IDC.

        Args:
            SeriesInstanceUID: string containing the value of DICOM SeriesInstanceUID for a series
            available in IDC

            StudyInstanceUID: string containing the value of DICOM SeriesInstanceUID for a series
            available in IDC

            viewer_selector: string containing the name of the viewer to use. Must be one of the following:
            ohif_v2, ohif_v2, or slim. If not provided, default viewers will be used. 

        Returns:
            string containing the IDC viewer URL for the given SeriesInstanceUID
        """

        if seriesInstanceUID is None and studyInstanceUID is None:
            raise ValueError("Either SeriesInstanceUID or StudyInstanceUID, or both, must be provided.")

        if seriesInstanceUID not in self.index['SeriesInstanceUID'].values:
            raise ValueError("SeriesInstanceUID not found in IDC index.")
        
        if studyInstanceUID is not None and studyInstanceUID not in self.index['StudyInstanceUID'].values:
            raise ValueError("StudyInstanceUID not found in IDC index.")
        
        if viewer_selector is not None and viewer_selector not in ['ohif_v2', 'ohif_v3', 'slim']:
            raise ValueError("viewer_selector must be one of 'ohif_v2', 'ohif_v3' or 'slim'.")

        modality = None

        if studyInstanceUID is None:

            query = f'''
            SELECT
                DISTINCT(StudyInstanceUID),
                Modality
            FROM
                index
            WHERE
                SeriesInstanceUID='{seriesInstanceUID}'
            '''
            query_result = self.sql_query(query)
            studyInstanceUID = query_result.StudyInstanceUID[0]
            modality = query_result.Modality[0]

        else:
            query = f'''
            SELECT
                DISTINCT(Modality)
            FROM
                index
            WHERE
                StudyInstanceUID='{studyInstanceUID}'
            '''
            query_result = self.sql_query(query)
            modality = query_result.Modality[0]

        if viewer_selector is None:
            if 'SM' in modality:
                viewer_selector = 'slim'
            else:
                viewer_selector = 'ohif_v2'

        if viewer_selector == "ohif_v2":
            if seriesInstanceUID is None:
                viewer_url = f'https://viewer.imaging.datacommons.cancer.gov/viewer/{studyInstanceUID}'
            else:
                viewer_url = f'https://viewer.imaging.datacommons.cancer.gov/viewer/{studyInstanceUID}?SeriesInstanceUID={seriesInstanceUID}'
        elif viewer_selector == "ohif_v3":
            if seriesInstanceUID is None:
                viewer_url = f'https://viewer.imaging.datacommons.cancer.gov/v3/viewer/?StudyInstanceUIDs={studyInstanceUID}'
            else:
                viewer_url = f'https://viewer.imaging.datacommons.cancer.gov/v3/viewer/?StudyInstanceUIDs={studyInstanceUID}&SeriesInstanceUID={seriesInstanceUID}'
        elif viewer_selector == "volview":
            # TODO! Not implemented yet
            pass
        elif viewer_selector == "slim":
            if seriesInstanceUID is None:
                viewer_url = f'https://viewer.imaging.datacommons.cancer.gov/slim/studies/{studyInstanceUID}'
            else:
                viewer_url = f'https://viewer.imaging.datacommons.cancer.gov/slim/studies/{studyInstanceUID}/series/{seriesInstanceUID}'

        return viewer_url

    def download_from_selection(self, downloadDir, dry_run=False, collection_id=None, patientId=None, studyInstanceUID=None, seriesInstanceUID=None):
        """Download the files corresponding to the selection. The filtering will be applied in sequence (but does it matter?) by first selecting the collection(s), followed by
        patient(s), study(studies) and series. If no filtering is applied, all the files will be downloaded.

        Args:
            collection_id: string or list of strings containing the values of collection_id to filter by
            patientId: string or list of strings containing the values of PatientID to filter by
            studyInstanceUID: string or list of strings containing the values of DICOM StudyInstanceUID to filter by
            seriesInstanceUID: string or list of strings containing the values of DICOM SeriesInstanceUID to filter by
            downloadDir: string containing the path to the directory to download the files to

        Returns:

        Raises:
            TypeError: If any of the parameters are not of the expected type
        """

        if collection_id is not None:
            if not isinstance(collection_id, str) and not isinstance(collection_id, list):
                raise TypeError("collection_id must be a string or list of strings")
        if patientId is not None:
            if not isinstance(patientId, str) and not isinstance(patientId, list):
                raise TypeError("patientId must be a string or list of strings")
        if studyInstanceUID is not None:
            if not isinstance(studyInstanceUID, str) and not isinstance(studyInstanceUID, list):
                raise TypeError("studyInstanceUID must be a string or list of strings")
        if seriesInstanceUID is not None:
            if not isinstance(seriesInstanceUID, str) and not isinstance(seriesInstanceUID, list):
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

        total_size = result_df['series_size_MB'].sum()
        logger.info("Total size of files to download: "+str(float(total_size)/1000)+"GB")
        logger.info("Total free space on disk: "+str(os.statvfs(downloadDir).f_bsize * os.statvfs(downloadDir).f_bavail / (1000*1000*1000))+"GB")

        if dry_run:
            logger.info("Dry run. Not downloading files. Rerun with dry_run=False to download the files.")
            return
        
        # Download the files
        # make temporary file to store the list of files to download
        manifest_file = os.path.join(downloadDir, 'download_manifest.s5cmd')
        for index, row in result_df.iterrows():
            with open(manifest_file, 'a') as f:
                f.write("cp --show-progress "+row['series_aws_url'] + " "+downloadDir+"\n")
        self.download_from_manifest(manifest_file, downloadDir)

    def download_from_manifest(self, manifestFile, downloadDir, quiet=True):
        """Download the files corresponding to the manifest file from IDC. The manifest file should be a text file with each line containing the s5cmd command to download the file. The URLs in the file must correspond to those in the AWS buckets!

        Args:
            manifest_file: string containing the path to the manifest file
            downloadDir: string containing the path to the directory to download the files to

        Returns:

        Raises:
        """

        downloadDir = os.path.abspath(downloadDir)

        if not os.path.exists(downloadDir):
            raise ValueError("Download directory does not exist.")
        if not os.path.exists(manifestFile):
            raise ValueError("Manifest does not exist.")

        # open manifest_file and read the first line that does not start from '#'
        with open(manifestFile, 'r') as f:
            for line in f:
                if not line.startswith('#'):
                    break
        pattern = r"(s3:\/\/.*)\/\*"
        match = re.search(pattern, line)
        if match is None:
            logger.error("Could not find the bucket URL in the first line of the manifest file.")
            return
        folder_url = match.group(1)
     
        cmd = [self.s5cmdPath, '--no-sign-request', '--endpoint-url', aws_endpoint_url, 'ls', folder_url]
        process = subprocess.run(cmd, capture_output=True, text=True)
        # check if output starts with ERROR
        if process.stderr and process.stderr.startswith('ERROR'):
            logger.debug("Folder not available in AWS. Checking in Google Cloud Storage.")

            cmd = [self.s5cmdPath, '--no-sign-request', '--endpoint-url', gcp_endpoint_url, 'ls', folder_url]
            process = subprocess.run(cmd, capture_output=True, text=True)
            if process.stderr and process.stdout.startswith('ERROR'):
                logger.debug("Folder not available in GCP. Manifest appears to be invalid.")
                raise ValueError
            else:
                endpoint_to_use = gcp_endpoint_url
        else:
            endpoint_to_use = aws_endpoint_url

        # create an updated manifest to include the specified destination directory
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_manifest_file:
            with open(manifestFile, 'r') as f:
                for line in f:
                    if not line.startswith('#'):
                        pattern = r"s3:\/\/.*\*"
                        match = re.search(pattern, line)
                        if folder_url is None:
                            logger.error("Could not find the bucket URL in the first line of the manifest file.")
                            return
                        folder_url = match.group(0)
                        temp_manifest_file.write(' cp '+folder_url+' '+downloadDir+'\n')

        cmd = [self.s5cmdPath, '--no-sign-request', '--endpoint-url', endpoint_to_use, 'run', temp_manifest_file.name]

        logger.debug("Running command: %s", ' '.join(cmd))
        process = subprocess.run(cmd, capture_output=(not quiet), text=(not quiet))
        logger.debug(process.stderr)
        logger.debug(process.stdout)
        if process.returncode == 0:
            logger.debug(f"Successfully downloaded files to {downloadDir}")
            logger.debug("Downloaded files: "+'\n'.join(os.listdir(downloadDir)))
        else:
            logger.error("Failed to download files.")

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
