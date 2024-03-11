import os
import pandas as pd
import re
import requests
import sys
import uuid
from google.cloud import bigquery


class IDCIndexManager:
    def __init__(self, project_id: str):
        """
        Initializes the IDCIndexManager class.

        This class is responsible for managing the index of the IDC (Imaging Data Commons) 
        in a Google Cloud BigQuery project. It sets up a BigQuery client for the specified 
        project and provides methods to keep idc-index upto date.

        Args:
            project_id (str): The ID of the Google Cloud project that the BigQuery client will be set up for.
        """
        print("Initializing IDCIndexManager...")
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)

    def get_latest_idc_release_version(self) -> int:
        """
        Retrieves the latest IDC release version.

        This function executes a SQL query on the `version_metadata` table in the `idc_current` 
        dataset of the BigQuery client. It retrieves the maximum `idc_version` and returns it as an integer.

        Returns:
            int: The latest IDC release version.
        """
        print("Getting latest IDC release version...")
        query = """
        SELECT
            MAX(idc_version) AS latest_idc_release_version
        FROM
            `bigquery-public-data.idc_current.version_metadata`
        """
        query_job = self.client.query(query)
        result = query_job.result()
        latest_idc_release_version = int(next(result).latest_idc_release_version)
        return latest_idc_release_version

    def extract_index_version(self, file_path: str) -> int:
        """
        Extracts the IDC version from a given file.

        This function reads a file line by line and searches for the line that contains 
        the IDC version. The IDC version is expected to be in the format "v<number>", and 
        this function extracts and returns the <number> part as an integer.

        Args:
            file_path (str): The path to the file from which to extract the IDC version.

        Returns:
            int: The extracted IDC version.
        """
        print(f"Extracting index version from {file_path}...")
        with open(file_path, "r") as file:
            for line in file:
                if "idc_version =" in line:
                    return int(re.findall(r'"v(\d+)"', line)[0])
         
    def update_index_version(self, file_path: str, latest_idc_release_version: int):
        """
        Updates the IDC version in a given file.

        This function reads a file line by line and searches for the line that contains 
        the IDC version assignment. It then updates this line with the latest IDC release version.

        Args:
            file_path (str): The path to the file in which to update the IDC version.
            latest_idc_release_version (int): The latest IDC release version to update in the file.

        """
        print(f"Updating index version in {file_path}...")
        with open(file_path, "r") as file:
            lines = file.readlines()
        with open(file_path, "w") as file:
            for line in lines:
                if "idc_version ="  in line:
                    line = f"idc_version = \"v{latest_idc_release_version}\"\n"
                file.write(line)

    def update_sql_queries_folder(
        self, dir: str, current_index_version: int, latest_idc_release_version: int
    ) -> None:
        """
        Updates SQL queries in a specified folder.

        This function iterates through files in the specified directory and identifies SQL files (those ending with `.sql`).
        It then replaces occurrences of the current IDC version (e.g., `idc_v17`) with the latest IDC release version (e.g., `idc_v18`).

        Args:
            dir (str): The path to the folder containing SQL files.
            current_index_version (int): The current IDC release version used in the SQL queries.
            latest_idc_release_version (int): The latest IDC release version to update in the SQL queries.

        Returns:
            None
        """
        print(f"Updating SQL queries from {dir}...")
        for file_name in os.listdir(dir):
            if file_name.endswith(".sql"):
                file_path = os.path.join(dir, file_name)
                with open(file_path, "r") as file:
                    sql_query = file.read()
                modified_sql_query = sql_query.replace(
                    f"idc_v{current_index_version}",
                    f"idc_v{latest_idc_release_version}",
                )
                with open(file_path, "w") as file:
                    file.write(modified_sql_query)

    def execute_sql_query(self, file_path: str) -> tuple[pd.DataFrame, str]:
        """
        Executes an SQL query from a specified file and returns the results as a DataFrame.

        This function reads the SQL query from the given file, executes it using the BigQuery client,
        and converts the results into a pandas DataFrame. Additionally, it generates a CSV file name
        based on the input file name.

        Args:
            file_path (str): The path to the file containing the SQL query.

        Returns:
            Tuple[pd.DataFrame, str]: A tuple containing the DataFrame with query results and the CSV file name.
        """
        print(f"Executing SQL query from {file_path}...")
        with open(file_path, "r") as file:
            sql_query = file.read()
        df = self.client.query(sql_query).to_dataframe()
        csv_file_name = f"{os.path.basename(file_path).split('.')[0]}.csv.zip"
        return df, csv_file_name

    def create_csv_zip_from_df(self, df: pd.DataFrame, csv_file_name: str) -> None:
        """
        Creates a compressed CSV file from a pandas DataFrame.

        This function takes a DataFrame and writes its contents to a CSV file. The CSV file is then
        compressed using the ZIP method. The resulting ZIP file contains the CSV data.

        Args:
            df (pd.DataFrame): The pandas DataFrame to be saved as a CSV.
            csv_file_name (str): The desired name for the resulting ZIP file (including the ".csv.zip" extension).

        Returns:
            None
        """
        print(f"Creating CSV zip file {csv_file_name}...")
        df.to_csv(csv_file_name, compression={"method": "zip"}, escapechar="\\")

    def run_queries_folder(self, dir: str) -> None:
        """
        Executes SQL queries from files in a specified folder.

        This function iterates through files in the specified directory and identifies SQL files (those ending with `.sql`).
        For each SQL file, it executes the query using the BigQuery client, converts the results into a pandas DataFrame,
        and creates a compressed CSV file containing the query results.

        Args:
            dir (str): The path to the folder containing SQL files.

        Returns:
            None
        """
        print(f"Running queries from {dir}...")
        for file_name in os.listdir(dir):
            if file_name.endswith(".sql"):
                file_path = os.path.join(dir, file_name)
                df, csv_file_name = self.execute_sql_query(file_path)
                self.create_csv_zip_from_df(df, csv_file_name)

    def set_multiline_output(self, name: str, value: str) -> None:
        """
        Sets multiline output for GitHub Actions.

        This function appends the specified `value` to the GitHub Actions output file
        (usually named `GITHUB_OUTPUT`). The `name` is used as a label for the output.

        Args:
            name (str): The label for the multiline output.
            value (str): The value to be appended to the output file.

        Returns:
            None
        """
        print(f"Setting multiline output {name}...")
        with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
            delimiter = uuid.uuid1()
            print(f"{name}<<{delimiter}", file=fh)
            print(value, file=fh)
            print(delimiter, file=fh)

    def run(self):
        """
        Executes the IDCIndexManager workflow.

        This function orchestrates the entire workflow for the IDCIndexManager. It retrieves the latest IDC release version,
        extracts the current index version from the `idc_index/index.py` file, and sets multiline outputs for GitHub Actions.

        Returns:
            None
        """
        print("Running IDCIndexManager...")
        latest_idc_release_version = self.get_latest_idc_release_version(
            "bigquery-public-data.idc_current.dicom_all_view"
        )
        print(f"Latest IDC release version: {latest_idc_release_version}")
        current_index_version = self.extract_index_version("idc_index/index.py")
        print(f"Current index version: {current_index_version}")
        self.set_multiline_output("current_index_version", int(current_index_version))
        self.set_multiline_output(
            "latest_idc_release_version", int(latest_idc_release_version)
        )

if __name__ == "__main__":
    manager = IDCIndexManager("gcp-project-id")
    manager.run()
