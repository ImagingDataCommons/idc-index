"""Copyright (c) 2024 Imaging Data Commons. All rights reserved.

idc-index: Package to query and download data from an index of ImagingDataCommons
"""


from __future__ import annotations

from ._version import version as __version__

__all__ = ["__version__"]

from .index import IDCClient

_ = IDCClient
