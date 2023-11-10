import json, string, os
import requests, logging
import pandas as pd
import platform
import urllib.request
import tarfile
import zipfile


class IDCClient:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'idc_data.csv.zip')
        self.index = pd.read_csv(file_path, dtype={14: str, 15: str,16: str})
        self.index = self.index.astype(str).replace('nan', '')
        self.s5cmdPath = None 
        self.s5cmdDownload()

        # Print after successful reading of index
        print("Successfully read the index.")


    def s5cmdDownload(self):
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
            print('s5cmd already exists. So not downloading again')
            return True

        # Download code based on the system detected
        for url in urls:
            try:
                print('Downloading s5cmd from', url)
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
                
                print(f's5cmd successfully downloaded and extracted, and is located at {self.s5cmdPath}')
                os.remove(filepath)
                return True  # Indicate successful download

            except Exception as e:
                print('Failed to download s5cmd:', e)
                # Attempt the next URL

        return False  # Indicate failure to download

    
    def get_collection_ids(self):
        unique_collections = self.index['collection_id'].unique()
        return unique_collections.tolist()
    
    def get_series_size(self, seriesInstanceUid):
        resp = self.index[['SeriesInstanceUID']==seriesInstanceUid]['series_size_MB'].iloc[0]
        return resp

    def get_patient(self, collection=None, outputFormat="json"):
        if collection is not None:
            print(collection)
            patient_df = self.index[self.index['collection_id'] == collection].copy()  

        else:
            patient_df = self.index.copy()  

        patient_df=patient_df.rename(columns={'collection_id':'Collection'})
        patient_df = patient_df[['PatientID', 'PatientSex', 'PatientAge']]
        patient_df = patient_df.groupby('PatientID').agg({
            'PatientSex': lambda x: ','.join(x[x != ''].unique()),
            'PatientAge': lambda x: ','.join(x[x != ''].unique())
        }).reset_index()

        patient_df = patient_df.drop_duplicates().sort_values(by='PatientID')
        # Convert DataFrame to a list of dictionaries for the API-like response
        idc_response = patient_df.to_dict(orient="records")

        logging.debug("Get patient response: %s", str(idc_response))

        return idc_response

    
    def get_patient_study(self, collection=None, patientId=None, studyInstanceUid=None, outputFormat="json"):
        if collection is not None:
            patient_study_df = self.index[self.index['collection_id'] == collection].copy()  
        elif patientId is not None:
            patient_study_df = self.index[self.index['PatientID'] == patientId].copy()  
        elif studyInstanceUid is not None:
            patient_study_df = self.index[self.index['StudyInstanceUID'] == studyInstanceUid].copy()  
        else:
            patient_study_df = self.index.copy()  

        patient_study_df['patient_study_size_MB'] = patient_study_df.groupby(['PatientID', 'StudyInstanceUID'])['series_size_MB'].transform('sum')
        patient_study_df['patient_study_series_count'] = patient_study_df.groupby(['PatientID', 'StudyInstanceUID'])['SeriesInstanceUID'].transform('count')
        patient_study_df['patient_study_instance_count'] = patient_study_df.groupby(['PatientID', 'StudyInstanceUID'])['instanceCount'].transform('count')

        patient_study_df = patient_study_df.rename(columns={'collection_id': 'Collection', 'patient_study_series_count': 'SeriesCount'})

        #patient_study_df = patient_study_df[['PatientID', 'PatientSex', 'Collection', 'PatientAge', 'StudyInstanceUID', 'StudyDate', 'StudyDescription', 'patient_study_size_MB', 'SeriesCount', 'patient_study_instance_count']]
        patient_study_df = patient_study_df[['StudyInstanceUID', 'StudyDate', 'StudyDescription', 'SeriesCount']]
        # Group by 'StudyInstanceUID' to make sure there is only one studyid in the GUI
        patient_study_df = patient_study_df.groupby('StudyInstanceUID').agg({
            'StudyDate': lambda x: ','.join(x[x != ''].unique()),
            'StudyDescription': lambda x: ','.join(x[x != ''].unique()),
            'SeriesCount': lambda x: int(x[x != ''].iloc[0]) if len(x[x != '']) > 0 else 0
        }).reset_index()

        patient_study_df = patient_study_df.drop_duplicates().sort_values(by=['StudyDate','StudyDescription','SeriesCount'])



        # Convert DataFrame to a list of dictionaries for the API-like response
        idc_response = patient_study_df.to_dict(orient="records")

        logging.debug("Get patient study response: %s", str(idc_response))

        return idc_response


    def get_series(self, collection=None, patientId=None, studyInstanceUID=None, modality=None, outputFormat="json"):
        if collection is not None:
            patient_series_df = self.index[self.index['collection_id'] == collection].copy()  # Make a copy
        elif patientId is not None:
            patient_series_df = self.index[self.index['PatientID'] == patientId].copy()  # Make a copy
        elif studyInstanceUID is not None:
            patient_series_df = self.index[self.index['StudyInstanceUID'] == studyInstanceUID].copy()  # Make a copy
        elif modality is not None:
            patient_series_df = self.index[self.index['Modality'] == modality].copy()  # Make a copy
        else:
            patient_series_df = self.index.copy()  # Make a copy

        patient_series_df = patient_series_df.rename(columns={'collection_id': 'Collection', 'instanceCount': 'instance_count'})
        patient_series_df['ImageCount']=1
        patient_series_df = patient_series_df[['StudyInstanceUID', 'SeriesInstanceUID', 'Modality', 'SeriesDate', 'Collection', 'BodyPartExamined', 'SeriesDescription', 'Manufacturer', 'ManufacturerModelName', 'series_size_MB','SeriesNumber', 'instance_count', 'ImageCount']]

        patient_series_df = patient_series_df.drop_duplicates().sort_values(by=['Modality','SeriesDate','SeriesDescription','BodyPartExamined', 'SeriesNumber'])
        # Convert DataFrame to a list of dictionaries for the API-like response
        idc_response = patient_series_df.to_dict(orient="records")

        logging.debug("Get series response: %s", str(idc_response))

        return idc_response

    def get_image(self, seriesInstanceUid, downloadDir, download=True):
        series_url = self.index[self.index['SeriesInstanceUID'] == seriesInstanceUid]['series_aws_location'].iloc[0]
        print('AWS Bucket Location: '+series_url)
        import subprocess

        cmd = [self.s5cmdPath, '--no-sign-request', '--endpoint-url', 'https://s3.amazonaws.com', 'cp', '--show-progress',
            series_url, downloadDir]

        if download:
            process = subprocess.run(cmd, capture_output=True, text=True)
            print(process.stderr)
            if process.returncode == 0:
                print(f"Successfully downloaded files to {downloadDir}")
            else:
                print("Failed to download files.")

