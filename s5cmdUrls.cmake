
# Checksum copied from "s5cmd_checksums.txt" associated with the s5cmd GitHub release

set(version "2.2.2")

set(linux32_filename    "s5cmd_${version}_Linux-32bit.tar.gz")
set(linux32_sha256      "dc9ebe570fb5abcf5781511901d93425879022d56e73ab44dd32c45b2bfbc04b")

set(linux64_filename    "s5cmd_${version}_Linux-64bit.tar.gz")
set(linux64_sha256      "a15f83d2a6dc091e43b2a120f29f8f6c86d146c381766c0197ec75d7985af2b6")

set(linuxarm64_filename "s5cmd_${version}_Linux-arm64.tar.gz")
set(linuxarm64_sha256   "eabf18082398c332d33c692d383a889be204b1e7716f820e014bf11474ad345b")

set(macos64_filename    "s5cmd_${version}_macOS-64bit.tar.gz")
set(macos64_sha256      "5503a3308e239f081e5238e0af57958ae618e0de8b9c71142fe80f38be77e1c7")

set(macosarm64_filename "s5cmd_${version}_macOS-arm64.tar.gz")
set(macosarm64_sha256   "fa3ae7e093fd6ac8a5236a000d5373779eb403c57ee955fc7da9549668644e38")

set(win32_filename      "s5cmd_${version}_Windows-32bit.zip")
set(win32_sha256        "ee667eb01b955a7dda588456bd102982f8344bed393a8b63b5d4c9c325e01349")

set(win64_filename      "s5cmd_${version}_Windows-64bit.zip")
set(win64_sha256        "f7c311907c78efa56e27a25fba1f87520754c402bbe1cb4901d3522f12a75497")


cmake_host_system_information(RESULT is_64bit QUERY IS_64BIT)

set(archive "linux32")
if(is_64bit)
  set(archive "linux64")
endif()

if(APPLE)
  set(archive "macos64")
endif()

if(WIN32)
  set(archive "win32")
  if(is_64bit AND NOT (${CMAKE_SYSTEM_PROCESSOR} STREQUAL "ARM64"))
    set(archive "win64")
  endif()
endif()

if(NOT DEFINED "${archive}_filename")
  message(FATAL_ERROR "Failed to determine which archive to download: '${archive}_filename' variable is not defined")
endif()

if(NOT DEFINED "${archive}_sha256")
  message(FATAL_ERROR "Could you make sure variable '${archive}_sha256' is defined ?")
endif()

set(s5cmd_archive_filename "${${archive}_filename}")
set(s5cmd_archive_sha256 "${${archive}_sha256}")

set(s5cmd_archive_url "https://github.com/peak/s5cmd/releases/download/v${version}/${s5cmd_archive_filename}")
