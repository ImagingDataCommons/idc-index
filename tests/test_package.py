from __future__ import annotations

import importlib.metadata

import idc_index as m


def test_version():
    assert importlib.metadata.version("idc_index") == m.__version__
