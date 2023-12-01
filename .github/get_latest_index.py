import os
import re
import requests
import sys
import uuid
from google.cloud import bigquery

class IDCIndexManager:
    def __init__(self, project_id):
        print("Initializing IDCIndexManager...")
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)

    def get_latest_idc_release_version(self, view_id):
        print("Getting latest IDC release version...")
        view = self.client.get_table(view_id)
        latest_idc_release_version=int(re.search(r"idc_v(\d+)", view.view_query).group(1))
        return latest_idc_release_version

    def extract_index_version(self, file_path):
        print(f"Extracting index version from {file_path}...")
        with open(file_path, "r") as file:
            for line in file:
                if "def get_idc_version(self):" in line:
                    return int(re.findall(r"v(\d+)", next(file))[0])

    def update_index_version(self, file_path, latest_idc_release_version):
        print(f"Updating index version in {file_path}...")
        with open(file_path, "r") as file:
            lines = file.readlines()
        with open(file_path, "w") as file:
            for i in range(len(lines)):
                if "def get_idc_version(self):" in lines[i]:
                    lines[i + 1] = re.sub(
                        r"v(\d+)", f"v{latest_idc_release_version}", lines[i + 1]
                    )
                file.write(lines[i])

    def update_sql_queries_folder(
        self, dir, current_index_version, latest_idc_release_version
    ):
        print(f"Updating SQL queries from {dir}...")
        for file_name in os.listdir(dir):
            if file_name.endswith(".sql"):
                file_path = os.path.join(dir, file_name)
                with open(file_path, "r") as file:
                    sql_query = file.read()
                modified_sql_query = sql_query.replace(
                    f"idc_v{current_index_version}", f"idc_v{latest_idc_release_version}"
                )
                with open(file_path, "w") as file:
                    file.write(modified_sql_query)
                return modified_sql_query

    def execute_sql_query(self, file_path):
        print(f"Executing SQL query from {file_path}...")
        with open(file_path, "r") as file:
            sql_query = file.read()
        df = self.client.query(sql_query).to_dataframe()
        csv_file_name = f"{os.path.basename(file_path).split('.')[0]}.csv.zip"
        return df, csv_file_name

    def create_csv_zip_from_df(self, df, csv_file_name):
        print(f"Creating CSV zip file {csv_file_name}...")
        df.to_csv(csv_file_name, compression={'method': 'zip'}, escapechar="\\")

    def run_queries_folder(self, dir):
        print(f"Running queries from {dir}...")
        for file_name in os.listdir(dir):
            if file_name.endswith(".sql"):
                file_path = os.path.join(dir, file_name)
                df, csv_file_name = self.execute_sql_query(file_path)
                self.create_csv_zip_from_df(df, csv_file_name)

    def set_multiline_output(self, name, value):
        print(f"Setting multiline output {name}...")
        with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
            delimiter = uuid.uuid1()
            print(f"{name}<<{delimiter}", file=fh)
            print(value, file=fh)
            print(delimiter, file=fh)

    def run(self):
        print("Running IDCIndexManager...")
        latest_idc_release_version = self.get_latest_idc_release_version("bigquery-public-data.idc_current.dicom_all_view")
        print(f"Latest IDC release version: {latest_idc_release_version}")
        current_index_version = self.extract_index_version("idc_index/index.py")
        print(f"Current index version: {current_index_version}")
        self.set_multiline_output("current_index_version", int(current_index_version))
        self.set_multiline_output("latest_idc_release_version", int(latest_idc_release_version))


if __name__ == "__main__":
    manager = IDCIndexManager("gcp-project-id")
    manager.run()
