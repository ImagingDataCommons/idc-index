"""Shared utilities for discovering and caching index metadata."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)


def fetch_indices_from_github(
    version: str, asset_endpoint_url: str, pre_installed_indices: dict[str, Any]
) -> dict[str, Any]:
    """Fetch available indices and their schemas from GitHub releases."""
    indices = pre_installed_indices.copy()

    # Fetch schemas for pre-installed indices
    for index_name in list(pre_installed_indices.keys()):
        json_url = f"{asset_endpoint_url}/{index_name}.json"
        try:
            schema_response = requests.get(json_url, timeout=30)
            if schema_response.status_code == 200:
                schema_data = schema_response.json()
                description = schema_data.get(
                    "table_description", indices[index_name]["description"]
                )
                indices[index_name]["description"] = description
                indices[index_name]["table_description"] = schema_data.get(
                    "table_description"
                )
                indices[index_name]["columns"] = schema_data.get("columns", [])
                logger.debug(f"Fetched schema for pre-installed index {index_name}")
        except Exception as e:
            logger.debug(f"Error fetching schema for {index_name}: {e}")

    # Discover additional indices from GitHub releases
    try:
        api_url = f"https://api.github.com/repos/ImagingDataCommons/idc-index-data/releases/tags/{version}"
        logger.debug(f"Querying GitHub API: {api_url}")
        response = requests.get(api_url, timeout=30)

        if response.status_code == 200:
            release_data = response.json()
            assets = release_data.get("assets", [])
            parquet_assets = [
                asset["name"] for asset in assets if asset["name"].endswith(".parquet")
            ]

            for parquet_name in parquet_assets:
                index_name = parquet_name.replace(".parquet", "")
                if index_name in pre_installed_indices:
                    continue

                json_url = f"{asset_endpoint_url}/{index_name}.json"
                description = f"Index table: {index_name}"
                schema_data = None

                try:
                    schema_response = requests.get(json_url, timeout=30)
                    if schema_response.status_code == 200:
                        schema_data = schema_response.json()
                        description = schema_data.get("table_description", description)
                except Exception as e:
                    logger.warning(f"Error fetching schema for {index_name}: {e}")

                indices[index_name] = {
                    "description": description,
                    "installed": False,
                    "url": f"{asset_endpoint_url}/{parquet_name}",
                    "file_path": None,
                }

                if schema_data:
                    indices[index_name]["table_description"] = schema_data.get(
                        "table_description"
                    )
                    indices[index_name]["columns"] = schema_data.get("columns", [])

    except Exception as e:
        logger.warning(f"Error during index discovery: {e}")

    return indices


def save_indices_cache(
    cache_file_path: str, version: str, indices: dict[str, Any]
) -> None:
    """Save indices metadata to cache file."""
    try:
        os.makedirs(os.path.dirname(cache_file_path), exist_ok=True)
        cache_data = {"version": version, "indices": indices}
        with open(cache_file_path, "w") as f:
            json.dump(cache_data, f, indent=2)
        logger.debug(f"Cached indices list to {cache_file_path}")
    except Exception as e:
        logger.warning(f"Failed to cache indices list: {e}")


def load_indices_cache(cache_file_path: str) -> dict[str, Any] | None:
    """Load indices metadata from cache file."""
    if not os.path.exists(cache_file_path):
        return None
    try:
        with open(cache_file_path) as f:
            cache_data = json.load(f)
            if "version" in cache_data and "indices" in cache_data:
                return cache_data
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to read indices cache: {e}")
    return None
