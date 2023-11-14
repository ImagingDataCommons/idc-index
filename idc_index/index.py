import os
import logging
import pandas as pd
import platform
import urllib.request
import subprocess
import tarfile
import zipfile


class IDCClient:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'idc_data.csv.zip')
        self.index = pd.read_csv(file_path, dtype=str, encoding='utf-8')
        self.index = self.index.astype(str).replace('nan', '')
        self.index['series_size_MB'] = self.index['series_size_MB'].astype(float)
        self.s5cmdPath = None 
        self._setup_s5cmd()

        # Print after successful reading of index
        logging.debug("Successfully read the index.")


    def _setup_s5cmd(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        s5cmdTargetDirectory = current_dir  # Save s5cmd in the directory with the IDC data file

        # List of mirror sites to attempt downloading s5cmd pre-built binaries from
        s5cmd_version = "2.2.2"
        system = platform.system()

        urls = []

        if system == "Windows":
            urls.append(f'https://github.com/peak/s5cmd/releases/download/v{s5cmd_version}/s5cmd_{s5cmd_version}_Windows-64bit.zip')
            self.s5cmdPath = os.path.join(s5cmdTargetDirectory, 's5cmd.exe')
        elif system == "Darwin":
            urls.append(f'https://github.com/peak/s5cmd/releases/download/v{s5cmd_version}/s5cmd_{s5cmd_version}_macOS-64bit.tar.gz')
            self.s5cmdPath = os.path.join(s5cmdTargetDirectory, 's5cmd')
        else:
            urls.append(f'https://github.com/peak/s5cmd/releases/download/v{s5cmd_version}/s5cmd_{s5cmd_version}_Linux-64bit.tar.gz')
            self.s5cmdPath = os.path.join(s5cmdTargetDirectory, 's5cmd')

        # Check if the file already exists
        if os.path.exists(self.s5cmdPath):
            logging.debug('s5cmd already exists. So not downloading again')
            return True

        # Download code based on the system detected
        for url in urls:
            try:
                logging.debug('Downloading s5cmd from', url)
                response = urllib.request.urlopen(url)

                # Downloading s5cmd to the current directory
                filepath = os.path.join(current_dir, os.path.basename(url))
                with open(filepath, 'wb') as f:
                    f.write(response.read())

                # Extract the s5cmd package
                if filepath.endswith('.zip'):
                    with zipfile.ZipFile(filepath, 'r') as zip_ref:
                        zip_ref.extractall(s5cmdTargetDirectory)
                else:
                    with tarfile.open(filepath, 'r:gz') as tar_ref:
                        tar_ref.extractall(s5cmdTargetDirectory)
                
                logging.debug(f's5cmd successfully downloaded and extracted, and is located at {self.s5cmdPath}')
                os.remove(filepath)
                return True  # Indicate successful download

            except Exception as e:
                logging.error('Failed to download s5cmd:', e)
                # Attempt the next URL

        return False  # Indicate failure to download

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
        return "v16";
    
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

        logging.debug("Get patient response: %s", str(response))

        return response

    """returns one row per distinct value of StudyInstanceUID
    """
    
    def get_dicom_studies(self, patientId, outputFormat="dict"):
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
                
        logging.debug("Get patient study response: %s", str(response))

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
            patient_series_df = patient_series_df.rename(columns={'collection_id': 'Collection', 'instanceCount': 'instance_count'})
            patient_series_df['ImageCount']=1
            patient_series_df = patient_series_df[['StudyInstanceUID', 'SeriesInstanceUID', 'Modality', 'SeriesDate', 'Collection', 'BodyPartExamined', 'SeriesDescription', 'Manufacturer', 'ManufacturerModelName', 'series_size_MB','SeriesNumber', 'instance_count', 'ImageCount']]

            patient_series_df = patient_series_df.drop_duplicates().sort_values(by=['Modality','SeriesDate','SeriesDescription','BodyPartExamined', 'SeriesNumber'])
            # Convert DataFrame to a list of dictionaries for the API-like response
            if outputFormat == "dict":
                response = patient_series_df.to_dict(orient="records")
            else:
                response = patient_series_df
        logging.debug("Get series response: %s", str(response))

        return response

    def download_dicom_series(self, seriesInstanceUID, downloadDir, dry_run=False, quiet=True):
        series_url = self.index[self.index['SeriesInstanceUID'] == seriesInstanceUID]['series_aws_location'].iloc[0]
        logging.debug('AWS Bucket Location: '+series_url)

        cmd = [self.s5cmdPath, '--no-sign-request', '--endpoint-url', 'https://s3.amazonaws.com', 'cp', '--show-progress',
            series_url, downloadDir]

        if not dry_run:
            process = subprocess.run(cmd, capture_output=True, text=True)
            if not quiet:
                print(process.stderr)
            if process.returncode == 0:
                logging.debug(f"Successfully downloaded files to {downloadDir}")
            else:
                logging.error("Failed to download files.")

    """Download the files corresponding to the selection. The filtering will be applied in sequence (but does it matter?) by first selecting the collection(s), followed by
    patient(s), study(studies) and series. If no filtering is applied, all the files will be downloaded.

    Args:
        collection_id: string or list of strings containing the values of collection_id to filter by
        patientId: string or list of strings containing the values of PatientID to filter by
        studyInstanceUID: string or list of strings containing the values of DICOM StudyInstanceUID to filter by
        downloadDir: string containing the path to the directory to download the files to

    Returns:

    Raises:
        TypeError: If any of the parameters are not of the expected type
    """
    def download_from_selection(self, downloadDir=None, dry_run=True, collection_id=None, patientId=None, studyInstanceUID=None):
        if collection_id is not None:
            if not isinstance(collection_id, str) and not isinstance(collection_id, list):
                raise TypeError("collection_id must be a string or list of strings")
        if patientId is not None:
            if not isinstance(patientId, str) and not isinstance(patientId, list):
                raise TypeError("collection_id must be a string or list of strings")
        if studyInstanceUID is not None:
            if not isinstance(studyInstanceUID, str) and not isinstance(studyInstanceUID, list):
                raise TypeError("collection_id must be a string or list of strings")

        if collection_id is not None:
            result_df = self._filter_by_collection_id(self.index, collection_id)
        else:
            result_df = self.index

        if patientId is not None:
            result_df = self._filter_by_patient_id(result_df, patientId)

        if studyInstanceUID is not None:
            result_df = self._filter_by_dicom_study_uid(result_df, studyInstanceUID)

        total_size = result_df['series_size_MB'].sum()
        logging.info("Total size of files to download: ", float(total_size)/1024, "GB")
        logging.info("Total free space on disk: ", os.statvfs(downloadDir).f_bsize * os.statvfs(downloadDir).f_bavail / 1024 / 1024 / 1024, "GB")

        if dry_run:
            logging.info("Dry run. Not downloading files. Rerun with dry_run=False to download the files.")
            return
        
        # Download the files
        # make temporary file to store the list of files to download
        manifest_file = os.path.join(downloadDir, 'download_manifest.s5cmd')
        for index, row in result_df.iterrows():
            with open(manifest_file, 'a') as f:
                f.write("cp --show-progress "+row['series_aws_location'] + " "+downloadDir+"\n")
        self.download_from_manifest(manifest_file, downloadDir)

    """Download the files corresponding to the manifest file from IDC. The manifest file should be a text file with each line containing the s5cmd command to download the file. The URLs in the file must correspond to those in the AWS buckets!

    Args:
        manifest_file: string containing the path to the manifest file
        downloadDir: string containing the path to the directory to download the files to

    Returns:

    Raises:
    """
    def download_from_manifest(self, manifest_file, downloadDir):
        cmd = [self.s5cmdPath, '--no-sign-request', '--endpoint-url', 'https://s3.amazonaws.com', 'run',
            manifest_file, downloadDir]
        process = subprocess.run(cmd, capture_output=True, text=True)
        logging.info(process.stderr)
        if process.returncode == 0:
            logging.debug(f"Successfully downloaded files to {downloadDir}")
        else:
            logging.error("Failed to download files.")
