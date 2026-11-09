cmake_minimum_required(VERSION 3.28)
if(POLICY CMP0207)
    cmake_policy(SET CMP0207 NEW)
endif()
if(NOT WIN32)
    message(FATAL_ERROR "Windows dependency collection must run on Windows")
endif()
if(NOT EXISTS "${EXECUTABLE}")
    message(FATAL_ERROR "Missing GROMACS executable: ${EXECUTABLE}")
endif()
file(GET_RUNTIME_DEPENDENCIES
    EXECUTABLES "${EXECUTABLE}"
    RESOLVED_DEPENDENCIES_VAR dependencies
    UNRESOLVED_DEPENDENCIES_VAR missing
    DIRECTORIES "$ENV{CUDA_PATH}/bin" "$ENV{CUDA_PATH}/bin/x64"
    PRE_EXCLUDE_REGEXES "[Aa][Pp][Ii]-[Mm][Ss]-.*" "[Ee][Xx][Tt]-[Mm][Ss]-.*" "[Nn][Vv][Cc][Uu][Dd][Aa]\\.[Dd][Ll][Ll]"
    POST_EXCLUDE_REGEXES ".*[/\\\\][Ww][Ii][Nn][Dd][Oo][Ww][Ss][/\\\\][Ss][Yy][Ss][Tt][Ee][Mm]32[/\\\\].*")
if(missing)
    message(FATAL_ERROR "Unresolved runtime dependencies: ${missing}")
endif()
foreach(dependency IN LISTS dependencies)
    file(COPY "${dependency}" DESTINATION "${OUTPUT_DIRECTORY}")
endforeach()
