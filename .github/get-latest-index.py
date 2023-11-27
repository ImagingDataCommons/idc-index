import os
import re
import requests
import sys
from google.cloud import bigquery
from github import Github

# Set up BigQuery client
project_id = "idc-external-025"
client = bigquery.Client(project=project_id)
owner='ImagingDataCommons'
# Set up GitHub client
g = Github(os.environ["GITHUB_TOKEN"])
repo = g.get_repo(f"{owner}/idc-index")

def extract_index_version(file_path):
    with open(file_path, "r") as file:
        for line in file:
            if "def get_idc_version(self):" in line:
                return int(re.findall(r"v(\d+)", next(file))[0])

def update_index_version(file_path, latest_idc_release_version):
    with open(file_path, "r") as file:
        lines = file.readlines()

    with open(file_path, "w") as file:
        for line in lines:
            if "def get_idc_version(self):" in line:
                line = re.sub(r"v(\d+)", f"v{latest_idc_release_version}", line)
            file.write(line)

def execute_sql_query(sql_query):
    df = client.query(sql_query).to_dataframe()
    return df

def update_sql_query(file_path, current_index_version, latest_idc_release_version):
    with open(file_path, "r") as file:
        sql_query = file.read()

    if current_index_version < latest_idc_release_version:
        modified_sql_query = sql_query.replace(
            f"idc_v{current_index_version}", f"idc_v{latest_idc_release_version}"
        )

        df = execute_sql_query(modified_sql_query)
        csv_file_name = f"{os.path.basename(file_path).split('.')[0]}.csv.zip"
        df.to_csv(csv_file_name, compression='gzip', escapechar="\\")

        with open(file_path, "w") as file:
            file.write(modified_sql_query)
    else:
        raise ValueError('Current version is not less than the latest version')

    return modified_sql_query, csv_file_name

# Get latest IDC release version
view_id = "bigquery-public-data.idc_current.dicom_all_view"
view = client.get_table(view_id)
latest_idc_release_version = int(re.search(r"idc_v(\d+)", view.view_query).group(1))

# Initialize the release body with information about the latest IDC release
release_body = (
    "Found newer IDC release with version "
    + str(latest_idc_release_version)
    + ".\n"
)

# List to store information for release creation
release_info_list = []

# Iterate over all SQL query files in the 'queries/' directory
for file_name in os.listdir("queries/"):
    if file_name.endswith(".sql"):
        file_path = os.path.join("queries/", file_name)
        current_index_version = extract_index_version('idc_index/index.py')
        modified_sql_query, csv_file_name = update_sql_query(file_path, current_index_version, latest_idc_release_version)
        if current_index_version < latest_idc_release_version:
            # Append information for each query to the release body
            release_body += (
                "\nUpdating the index from idc_v"
                + str(current_index_version)
                + " to idc_v"
                + str(latest_idc_release_version)
                + "\nThe sql query used for generating the new csv index is \n```\n"
                + modified_sql_query
                + "\n```"
            )
            release_info_list.append((csv_file_name,))

# Update the index.py file with the latest IDC release version
update_index_version('idc_index/index.py', latest_idc_release_version)

# Check if any updates were made before creating a release
if release_info_list:
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # Check if a release with the tag 'latest' already exists
    response = requests.get(
        f"https://api.github.com/repos/{owner}/idc-index/releases/tags/latest",
        headers=headers,
    )

    # If a release with the tag 'latest' exists, delete it
    if response.status_code == 200:
        release_id = response.json()["id"]
        requests.delete(
            f"https://api.github.com/repos/{owner}/idc-index/releases/{release_id}",
            headers=headers,
        )

    # Create a new release
    data = {
        "tag_name": 'latest',
        "target_commitish": "main",
        "body": release_body,
        "draft": False,
        "prerelease": True,
        "generate_release_notes": False,
    }
    response = requests.post(
        f"https://api.github.com/repos/{owner}/idc-index/releases",
        headers=headers,
        json=data,
    )

    # Check if release was created successfully
    if response.status_code == 201:
        # Get upload URL for release assets
        upload_url = response.json()["upload_url"]
        upload_url = upload_url[: upload_url.find("{")]

        # Upload CSV files as release assets
        for csv_file_name in release_info_list:
            upload_url_for_file = upload_url + "?name=" + csv_file_name[0]
            headers["Content-Type"] = "application/octet-stream"
            with open(csv_file_name[0], "rb") as data:
                response = requests.post(upload_url_for_file, headers=headers, data=data)

                # Check if asset was uploaded successfully
                if response.status_code != 201:
                    print("Error uploading asset: " + response.text)
                    sys.exit(1)
    else:
        print("Error creating release: " + response.text)
        sys.exit(1)
else:
    print("No updates were found.")


# Create a new branch
new_branch = repo.create_git_ref(ref=f"refs/heads/update-v{latest_idc_release_version}", sha=repo.get_branch("main").commit.sha)

# Commit changes to the new branch
for file_name in os.listdir("queries/"):
    if file_name.endswith(".sql"):
        file_path = os.path.join("queries/", file_name)
        repo.update_file(path=file_path, message=f"Update to v{latest_idc_release_version}", content=open(file_path, 'r').read(), sha=repo.get_contents(file_path, ref=new_branch.ref).sha, branch=new_branch.ref)

repo.update_file(path='idc_index/index.py', message=f"Update to v{latest_idc_release_version}", content=open('idc_index/index.py', 'r').read(), sha=repo.get_contents('idc_index/index.py', ref=new_branch.ref).sha, branch=new_branch.ref)

# Create a pull request
repo.create_pull(title=f"Update to v{latest_idc_release_version}", body="This PR updates the SQL queries and index.py to the latest IDC release version.", head=new_branch.ref, base="main")
