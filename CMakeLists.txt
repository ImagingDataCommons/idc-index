cmake_minimum_required(VERSION 3.15...3.26)
project(${SKBUILD_PROJECT_NAME} LANGUAGES NONE)


set(idc_index_release_version "0.3.2")
set(idc_index_data_url "https://github.com/ImagingDataCommons/idc-index/releases/download/${idc_index_release_version}/idc_index.csv.zip")
set(idc_index_data_sha256 "70ec9f915686a27bee3098163b8695c69c8696c05bfb7bd76943a24024cdeeb9")

#
# Download and install index
#
set(download_dir "${PROJECT_BINARY_DIR}")
include(FetchContent)
FetchContent_Populate(s5cmd
  URL ${idc_index_data_url}
  URL_HASH SHA256=${idc_index_data_sha256}
  DOWNLOAD_DIR ${download_dir}
  DOWNLOAD_NO_EXTRACT TRUE
  )
install(FILES "${download_dir}/idc_index.csv.zip" DESTINATION "idc_index/idc_index_data")
