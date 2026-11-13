"""Tests for installing clinical tables, using a local clinical_index and tables.

The S3 copy is replaced with a mock, so these tests need no network access.
"""

from __future__ import annotations

import subprocess
from unittest import mock

import pandas as pd
import pytest
from idc_index import IDCClient

TABLES = ["table_a", "table_b"]


@pytest.fixture(scope="module")
def client():
    return IDCClient()


@pytest.fixture
def clinical(client, tmp_path, monkeypatch):
    """Point the client at a clinical_index on disk that has not been loaded yet."""
    index_path = tmp_path / "clinical_index.parquet"
    pd.DataFrame({"collection_id": ["c", "c"], "short_table_name": TABLES}).to_parquet(
        index_path
    )
    monkeypatch.setitem(
        client.indices_overview,
        "clinical_index",
        {
            **client.indices_overview["clinical_index"],
            "installed": True,
            "file_path": str(index_path),
        },
    )
    monkeypatch.setattr(client, "idc_data_dir", str(tmp_path / "idc"))
    monkeypatch.setattr(client, "clinical_index", None)
    monkeypatch.setattr(client, "clinical_data_dir", None)
    run = mock.Mock(
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="")
    )
    monkeypatch.setattr("idc_index.index.subprocess.run", run)
    return run, tmp_path / "idc" / "clinical_data"


def write_table(clinical_data_dir, table_name):
    table_dir = clinical_data_dir / table_name
    table_dir.mkdir(parents=True)
    pd.DataFrame({"value": [table_name]}).to_parquet(table_dir / "000000000000.parquet")


def test_fetch_uses_tables_on_disk(client, clinical):
    run, clinical_data_dir = clinical
    for table_name in TABLES:
        write_table(clinical_data_dir, table_name)

    client.fetch_index("clinical_index")

    run.assert_not_called()
    assert client.clinical_data_dir == str(clinical_data_dir)


def test_fetch_downloads_when_a_table_is_missing(client, clinical):
    run, clinical_data_dir = clinical
    write_table(clinical_data_dir, TABLES[0])

    client.fetch_index("clinical_index")

    run.assert_called_once()
    args = run.call_args.args[0]
    assert args[1:3] == ["--no-sign-request", "cp"]
    assert args[-1] == str(clinical_data_dir)
    assert client.clinical_data_dir == str(clinical_data_dir)


def test_get_clinical_table_without_fetch_index(client, clinical):
    run, clinical_data_dir = clinical
    for table_name in TABLES:
        write_table(clinical_data_dir, table_name)

    table = client.get_clinical_table(TABLES[1])

    run.assert_not_called()
    assert table["value"].tolist() == [TABLES[1]]
