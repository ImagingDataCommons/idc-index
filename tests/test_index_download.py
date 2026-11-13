"""Tests for the hash-checked index download used by IDCClient.fetch_index."""

from __future__ import annotations

import base64
import hashlib
import os
import stat
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import requests
from idc_index import IDCClientIndexVerificationError
from idc_index.index import _download_verified, _md5_from_goog_hash

BODY = b"PAR1" + bytes(range(256)) * 64 + b"PAR1"
BODY_MD5 = base64.b64encode(hashlib.md5(BODY).digest()).decode("ascii")
OTHER_MD5 = base64.b64encode(hashlib.md5(b"something else").digest()).decode("ascii")

# path -> (status, headers, body, Content-Length to declare)
ROUTES = {
    # GCS sends one x-goog-hash header per hash type
    "/ok": (
        200,
        [("x-goog-hash", "crc32c=AAAAAA=="), ("x-goog-hash", f"md5={BODY_MD5}")],
        BODY,
        len(BODY),
    ),
    "/wrong-md5": (
        200,
        [("x-goog-hash", "crc32c=AAAAAA=="), ("x-goog-hash", f"md5={OTHER_MD5}")],
        BODY,
        len(BODY),
    ),
    # composite objects report only CRC32C
    "/crc32c-only": (200, [("x-goog-hash", "crc32c=AAAAAA==")], BODY, len(BODY)),
    "/no-hash": (200, [], BODY, len(BODY)),
    # connection closes before the declared length is sent
    "/truncated": (
        200,
        [("x-goog-hash", f"md5={BODY_MD5}")],
        BODY[:1000],
        len(BODY),
    ),
    "/missing": (404, [], b"", 0),
}


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status, headers, body, length = ROUTES[self.path]
        self.send_response(status)
        for name, value in headers:
            self.send_header(name, value)
        self.send_header("Content-Length", str(length))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


@pytest.fixture(scope="module")
def server_url():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        (f"crc32c=AAAAAA==, md5={BODY_MD5}", BODY_MD5),
        (f"md5={BODY_MD5},crc32c=AAAAAA==", BODY_MD5),
        ("crc32c=AAAAAA==", None),
        ("", None),
        (None, None),
    ],
)
def test_md5_from_goog_hash(header, expected):
    assert _md5_from_goog_hash(header) == expected


def test_download_matching_md5(server_url, tmp_path):
    dest = tmp_path / "sub" / "index.parquet"
    _download_verified(f"{server_url}/ok", str(dest))
    assert dest.read_bytes() == BODY
    assert list(dest.parent.iterdir()) == [dest]


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows has no POSIX permission bits"
)
def test_download_honors_umask(server_url, tmp_path):
    dest = tmp_path / "index.parquet"
    old_umask = os.umask(0o022)
    try:
        _download_verified(f"{server_url}/ok", str(dest))
    finally:
        os.umask(old_umask)
    assert stat.S_IMODE(dest.stat().st_mode) == 0o644


@pytest.mark.parametrize("route", ["/wrong-md5", "/crc32c-only", "/no-hash"])
def test_download_unverified_is_rejected(server_url, tmp_path, route):
    dest = tmp_path / "index.parquet"
    with pytest.raises(IDCClientIndexVerificationError):
        _download_verified(f"{server_url}{route}", str(dest))
    assert list(tmp_path.iterdir()) == []


def test_failed_download_keeps_existing_file(server_url, tmp_path):
    dest = tmp_path / "index.parquet"
    dest.write_bytes(b"previous")
    with pytest.raises(IDCClientIndexVerificationError):
        _download_verified(f"{server_url}/wrong-md5", str(dest))
    assert dest.read_bytes() == b"previous"
    assert list(tmp_path.iterdir()) == [dest]


def test_truncated_download_leaves_no_file(server_url, tmp_path):
    dest = tmp_path / "index.parquet"
    with pytest.raises(requests.RequestException):
        _download_verified(f"{server_url}/truncated", str(dest))
    assert list(tmp_path.iterdir()) == []


def test_http_error_is_raised(server_url, tmp_path):
    dest = tmp_path / "index.parquet"
    with pytest.raises(requests.HTTPError):
        _download_verified(f"{server_url}/missing", str(dest))
    assert list(tmp_path.iterdir()) == []
