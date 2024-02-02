cmake_minimum_required(VERSION 3.15...3.26)
project(${SKBUILD_PROJECT_NAME} LANGUAGES NONE)

function(_check_archive dest_file expected_sha256 output_var)
  get_filename_component(filename ${dest_file} NAME)
  message(STATUS "Checking ${filename}")

  if(NOT EXISTS ${dest_file})
    message(STATUS "Checking ${filename} - nonexistent")
    set(${output_var} "nonexistent" PARENT_SCOPE)
    return()
  endif()

  file(SHA256 ${dest_file} current_hash)
  if(NOT ${current_hash} STREQUAL ${expected_sha256})
    message(STATUS "Checking ${filename} - expired")
    set(${output_var} "expired" PARENT_SCOPE)
    return()
  endif()

  message(STATUS "Checking ${filename} - up-to-date")
  set(${output_var} "ok" PARENT_SCOPE)
endfunction()

# Set in the current scope the following variables:
# - s5cmd_archive_url
# - s5cmd_archive_sha256
include(${CMAKE_CURRENT_SOURCE_DIR}/s5cmdUrls.cmake)

#
# Download archive
#
cmake_path(GET s5cmd_archive_url FILENAME archive_filename)
set(destination_file "${CMAKE_CURRENT_BINARY_DIR}/${archive_filename}")

_check_archive(${destination_file} ${s5cmd_archive_sha256} result)

if(result MATCHES "^(nonexistent|expired)$")
  message(STATUS "Downloading ${s5cmd_archive_url}")
  file(
    DOWNLOAD
      ${s5cmd_archive_url}
      ${destination_file}
    EXPECTED_HASH SHA256=${s5cmd_archive_sha256}
    )
elseif(result STREQUAL "ok")
  # ok
else()
  message(FATAL_ERROR "Unknown result value: ${result}")
endif()

#
# Extract archive
#
set(executable_name "s5cmd${CMAKE_EXECUTABLE_SUFFIX}")

string(MAKE_C_IDENTIFIER ${archive_filename} extract_subdir)
set(extract_dir "${CMAKE_CURRENT_BINARY_DIR}/${extract_subdir}")
message(STATUS "Extracting ${archive_filename} into ${extract_dir}")
file(ARCHIVE_EXTRACT
  INPUT ${destination_file}
  DESTINATION ${extract_dir}
  PATTERNS "${executable_name}"
  VERBOSE
  )

set(s5cmd_package "idc_index/s5cmd")

message(STATUS "Copying ${executable_name} to ${s5cmd_package}")
file(COPY ${extract_dir}/${executable_name} DESTINATION ${PROJECT_SOURCE_DIR}/${s5cmd_package})

set(_permissions PERMISSIONS
  OWNER_READ OWNER_WRITE OWNER_EXECUTE
  GROUP_READ GROUP_EXECUTE
  WORLD_READ WORLD_EXECUTE
  )

message(STATUS "Changing ${executable_name} permissions to be executable")
file(CHMOD ${PROJECT_SOURCE_DIR}/${s5cmd_package}/${executable_name} ${_permissions})

install(PROGRAMS ${extract_dir}/${executable_name} DESTINATION "${s5cmd_package}" ${_permissions})
