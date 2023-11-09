from setuptools import setup, find_packages

setup(
    name="idc_index_vamsi",
    version="0.0.1",
    author="Vamsi Thiriveedhi",
    author_email="vamsikrishna1414@gmail.com",
    url="https://vamsithiriveedhi.com",
    description="An application that informs you of the time in different locations and timezones",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=["click", "pytz"],
    entry_points={"console_scripts": ["idc_index_vamsi = src.main:main"]},
)