"""CLI module for the IDC client.

This module provides command-line interface (CLI) commands to interact with the Imaging Data Commons (IDC) data.
"""
from __future__ import annotations

import logging
from pathlib import Path

import click

from . import index
from .index import IDCClient

# Set up logging for the CLI module
logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.DEBUG)
logger_cli = logging.getLogger("cli")
logger_cli.setLevel("WARNING")


@click.group()
def main():
    """Idc is a command line client to help download data from Imaging Data Commons."""


def set_log_level(log_level):
    """Set the logging level for the CLI module.

    Args:
        log_level (str): The logging level to set.
    """
    log_levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    logging_level = log_levels.get(log_level.lower(), logging.WARNING)
    logger_cli.debug(f"Setting the log level of index.py to {logging_level}")
    index.logger.setLevel(logging_level)


@main.command()
@click.option(
    "--download-dir",
    required=True,
    type=click.Path(),
    help="Path to the directory to download the files to.",
)
@click.option(
    "--dry-run",
    type=bool,
    default=False,
    help="If set, calculates the size of the cohort but download does not start.",
)
@click.option(
    "--collection-id",
    type=str,
    multiple=True,
    default=None,
    help="Collection ID(s) to filter by.",
)
@click.option(
    "--patient-id",
    type=str,
    multiple=True,
    default=None,
    help="Patient ID(s) to filter by.",
)
@click.option(
    "--study-instance-uid",
    type=str,
    multiple=True,
    default=None,
    help="DICOM StudyInstanceUID(s) to filter by.",
)
@click.option(
    "--series-instance-uid",
    type=str,
    multiple=True,
    default=None,
    help="DICOM SeriesInstanceUID(s) to filter by.",
)
@click.option(
    "--quiet",
    type=bool,
    default=True,
    help="If set, suppresses the output of the subprocess.",
)
@click.option(
    "--show-progress-bar",
    type=bool,
    default=True,
    help="If set, tracks the progress of download.",
)
@click.option(
    "--use-s5cmd-sync",
    type=bool,
    default=False,
    help="If set, will use s5cmd sync operation instead of cp when downloadDirectory is not empty; this can significantly improve the download speed if the content is partially downloaded.",
)
@click.option(
    "--log-level",
    type=click.Choice(
        ["debug", "info", "warning", "error", "critical"], case_sensitive=False
    ),
    default="info",
    help="Set the logging level for the CLI module.",
)
def download_from_selection(
    download_dir,
    dry_run,
    collection_id,
    patient_id,
    study_instance_uid,
    series_instance_uid,
    quiet,
    show_progress_bar,
    use_s5cmd_sync,
    log_level,
):
    """Download from a selection of collection(s), patient(s), study(studies) and series.

    The filtering will be applied in sequence by first selecting the collection(s), followed by
    patient(s), study(studies) and series. If no filtering is applied, all the files will be downloaded.
    """
    # Set the logging level for the CLI module
    set_log_level(log_level)
    # Create an instance of the IDCClient
    client = IDCClient()
    # Parse the input parameters and pass them to IDCClient's download_from_selection method
    collection_id = (
        [cid.strip() for cid in (",".join(collection_id)).split(",")]
        if collection_id
        else None
    )
    patient_id = (
        [pid.strip() for pid in (",".join(patient_id)).split(",")]
        if patient_id
        else None
    )
    study_instance_uid = (
        [uid.strip() for uid in (",".join(study_instance_uid)).split(",")]
        if study_instance_uid
        else None
    )
    series_instance_uid = (
        [uid.strip() for uid in (",".join(series_instance_uid)).split(",")]
        if series_instance_uid
        else None
    )
    logger_cli.debug("Inputs received from cli download:")
    logger_cli.debug(f"collection_id: {collection_id}")
    logger_cli.debug(f"patient_id: {patient_id}")
    logger_cli.debug(f"study_instance_uid: {study_instance_uid}")
    logger_cli.debug(f"series_instance_uid: {series_instance_uid}")
    logger_cli.debug(f"dry_run: {dry_run}")
    logger_cli.debug(f"quiet: {quiet}")
    logger_cli.debug(f"show_progress_bar: {show_progress_bar}")
    logger_cli.debug(f"use_s5cmd_sync: {use_s5cmd_sync}")

    client.download_from_selection(
        download_dir,
        dry_run=dry_run,
        collection_id=collection_id,
        patientId=patient_id,
        studyInstanceUID=study_instance_uid,
        seriesInstanceUID=series_instance_uid,
        quiet=quiet,
        show_progress_bar=show_progress_bar,
        use_s5cmd_sync=use_s5cmd_sync,
    )


@main.command()
@click.option(
    "--manifest-file",
    required=True,
    type=click.Path(),
    help="The path to the manifest file.",
)
@click.option(
    "--download-dir",
    required=True,
    type=click.Path(),
    help="Path to the directory to download the files to.",
)
@click.option(
    "--quiet",
    type=bool,
    default=True,
    help="If set, suppresses the output of the subprocess.",
)
@click.option(
    "--validate-manifest",
    type=bool,
    default=True,
    help="If True, validates the manifest for any errors. Defaults to True.",
)
@click.option(
    "--show-progress-bar",
    type=bool,
    default=True,
    help="If set, tracks the progress of download.",
)
@click.option(
    "--use-s5cmd-sync",
    type=bool,
    default=False,
    help="If set, will use s5cmd sync operation instead of cp when downloadDirectory is not empty; this can significantly improve the download speed if the content is partially downloaded.",
)
@click.option(
    "--log-level",
    type=click.Choice(
        ["debug", "info", "warning", "error", "critical"], case_sensitive=False
    ),
    default="info",
    help="Set the logging level for the CLI module.",
)
def download_from_manifest(
    manifest_file,
    download_dir,
    quiet,
    validate_manifest,
    show_progress_bar,
    use_s5cmd_sync,
    log_level,
):
    """Download the manifest file.

    In a series of steps, the manifest file is first validated to ensure every line contains a valid URL.
    It then gets the total size to be downloaded and runs the download process on one
    process and download progress on another process.
    """
    # Set the logging level for the CLI module
    set_log_level(log_level)
    # Create an instance of the IDCClient
    client = IDCClient()
    logger_cli.debug("Inputs received from cli manifest download:")
    logger_cli.debug(f"manifest_file_path: {manifest_file}")
    logger_cli.debug(f"download_dir: {download_dir}")
    logger_cli.debug(f"validate_manifest: {validate_manifest}")
    logger_cli.debug(f"show_progress_bar: {show_progress_bar}")
    logger_cli.debug(f"use_s5cmd_sync: {use_s5cmd_sync}")
    # Call IDCClient's download_from_manifest method with the provided parameters
    client.download_from_manifest(
        manifestFile=manifest_file,
        downloadDir=download_dir,
        quiet=quiet,
        validate_manifest=validate_manifest,
        show_progress_bar=show_progress_bar,
        use_s5cmd_sync=use_s5cmd_sync,
    )


@main.command()
@click.argument(
    "generic_argument",
    type=str,
)
def download(
    generic_argument,
):
    """Download content given the input parameter.

    Determine whether the input parameter corresponds to a file manifest or a list of collection_id, PatientID, StudyInstanceUID, or SeriesInstanceUID values, and download the corresponding files into the current directory. Default parameters will be used for organizing the downloaded files into folder hierarchy. Use `download_from_selection()` and `download_from_manifest()` functions if granular control over the download process is needed.
    """
    # Create an instance of the IDCClient
    client = IDCClient()

    download_dir = Path.cwd()

    if Path(generic_argument).is_file():
        # Parse the input parameters and pass them to IDC
        logger_cli.debug("Detected manifest file, downloading from manifest.")
        client.download_from_manifest(generic_argument, downloadDir=download_dir)
    # this is not a file manifest
    else:
        # check if the passed string contains commands
        if "," in generic_argument:
            item_ids = generic_argument.split(",")
        else:
            item_ids = [generic_argument]
        # this is a streamlined command, we will only check the first item, and will assume all other items are of the same kind
        if client.index["collection_id"].str.contains(item_ids[0]).any():
            logger_cli.debug("Downloading from collection_id")
            client.download_from_selection(
                collection_id=item_ids, downloadDir=download_dir
            )
        elif client.index["PatientID"].str.contains(item_ids[0]).any():
            logger_cli.debug("Downloading from PatientID")
            client.download_from_selection(patientId=item_ids, downloadDir=download_dir)
        elif client.index["StudyInstanceUID"].str.contains(item_ids[0]).any():
            logger_cli.debug("Downloading from StudyInstanceUID")
            client.download_from_selection(
                studyInstanceUID=item_ids, downloadDir=download_dir
            )
        elif client.index["SeriesInstanceUID"].str.contains(item_ids[0]).any():
            logger_cli.debug("Downloading from SeriesInstanceUID")
            client.download_from_selection(
                seriesInstanceUID=item_ids, downloadDir=download_dir
            )


if __name__ == "__main__":
    main()
