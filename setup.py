from setuptools import setup, find_packages
from setuptools.command.install import install
import os
import logging
import urllib.request
import subprocess
import platform
import urllib.request
import tarfile
import zipfile

package_version = "0.2.6"

# Read long description from README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        # Downloading s5cmd and csv index in the same location as the python modules
        save_location = os.path.join(self.install_lib, 'idc_index')

        # Create the directory if it doesn't exist
        os.makedirs(save_location, exist_ok=True)

        # Download the index file
        try:
            urllib.request.urlretrieve('https://github.com/ImagingDataCommons/idc-index/releases/download/'+package_version+'/idc_index.csv.zip', os.path.join(save_location, 'idc_index.csv.zip'))
            print(f"Downloaded index")
        except Exception as err:
            print(f"Something went wrong while downloading the index file: {err}")

        s5cmd_version = "2.2.2"
        system = platform.system()
        urls = []

        if system == "Windows":
            urls.append(f'https://github.com/peak/s5cmd/releases/download/v{s5cmd_version}/s5cmd_{s5cmd_version}_Windows-64bit.zip')
            s5cmd_path = os.path.join(save_location, 's5cmd.exe')
        elif system == "Darwin":
            urls.append(f'https://github.com/peak/s5cmd/releases/download/v{s5cmd_version}/s5cmd_{s5cmd_version}_macOS-64bit.tar.gz')
            s5cmd_path = os.path.join(save_location, 's5cmd')
        else:
            urls.append(f'https://github.com/peak/s5cmd/releases/download/v{s5cmd_version}/s5cmd_{s5cmd_version}_Linux-64bit.tar.gz')
            s5cmd_path = os.path.join(save_location, 's5cmd')

        for url in urls:
            try:
                print('Downloading s5cmd from', url)
                response = urllib.request.urlopen(url)

                # Downloading s5cmd to the current directory
                filepath = os.path.join(save_location, os.path.basename(url))
                with open(filepath, 'wb') as f:
                    f.write(response.read())

                # Extract the s5cmd package
                if filepath.endswith('.zip'):
                    with zipfile.ZipFile(filepath, 'r') as zip_ref:
                        zip_ref.extractall(save_location)
                else:
                    with tarfile.open(filepath, 'r:gz') as tar_ref:
                        tar_ref.extractall(save_location)

                print(f's5cmd successfully downloaded and extracted, and is located at {s5cmd_path}')
                os.remove(filepath)
                break  # Indicate successful download and exit the loop
            except Exception as e:
                logging.error('Failed to download s5cmd:', e)
setup(
    name='idc_index',
    version=package_version,
    packages=find_packages(),
    include_package_data=True,
    install_requires=['pandas', 'requests'],
    cmdclass={
        'install': PostInstallCommand,
    },
    # Metadata
    author='ImagingDataCommons',
    description='Package to query and download data from an index of ImagingDataCommons',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/ImagingDataCommons/idc-index',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta"
    ]
)
