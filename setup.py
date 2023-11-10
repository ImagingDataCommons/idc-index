from setuptools import setup, find_packages

# Read long description from README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='idc_index',
    version='0.0.3',
    packages=find_packages(),
    include_package_data=True,  
    install_requires=['pandas'],
    # Metadata
    author='Vamsi Thiriveedhi',
    author_email='vthiriveedhi@mgb.org',
    description='Package to query and download data from an index of ImagingDataCommons',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/vkt1414/idc_index',
    classifiers=[
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent"]
)
