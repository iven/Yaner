#
# Yaner: CMake build system template for Qt based projects
# Author: Iven Hsu <ivenvd AT gmail.com>
#

#Put here CPPs
SET(YANER_SRCS
    application.cc
    main.cc
    main_window.cc
)

SET(YANER_HDRS
    application.h
    main_window.h
    yaner.h
)

#Put here QRC files to be Rcc-ed
SET(YANER_RCC
    resources.qrc
    ../ts/resources-ts.qrc
)

#Put here UI files
SET(YANER_UIS
    main_window.ui
)

#include paths for vlmc
INCLUDE_DIRECTORIES(
  ${CMAKE_CURRENT_BINARY_DIR}
  ${CMAKE_CURRENT_BINARY_DIR}/src
  .
)

CONFIGURE_FILE(${CMAKE_SOURCE_DIR}/cmake/config.h.cmake ${CMAKE_CURRENT_BINARY_DIR}/config.h)

QT4_WRAP_UI(YANER_UIS_H ${YANER_UIS})
QT4_ADD_RESOURCES(YANER_RCC_SRCS ${YANER_RCC})
QT4_WRAP_CPP(YANER_MOC_SRCS ${YANER_HDRS})

IF(APPLE)
    SET(GUI_TYPE MACOSX_BUNDLE)
    SET(YANER_SRCS ${YANER_SRCS} ../share/yaner.icns)
    SET_SOURCE_FILES_PROPERTIES(../share/yaner.icns PROPERTIES
        MACOSX_PACKAGE_LOCATION Resources)
    SET(MACOSX_BUNDLE_ICON_FILE yaner.icns)
ENDIF(APPLE)

ADD_EXECUTABLE(yaner ${YANER_SRCS} ${YANER_MOC_SRCS} ${YANER_UIS_H} ${YANER_RCC_SRCS} )

# Add translations
ADD_DEPENDENCIES(yaner translations)

# Link the target against the Qt libraries
TARGET_LINK_LIBRARIES(yaner ${QT_LIBRARIES})

# Now we are done.

INSTALL(TARGETS yaner
        BUNDLE  DESTINATION ${YANER_BIN_DIR}
        RUNTIME DESTINATION ${YANER_BIN_DIR})

ADD_CUSTOM_COMMAND(
    OUTPUT ${CMAKE_SOURCE_DIR}/bin/yaner
    COMMAND ${CMAKE_COMMAND} copy ${CMAKE_CURRENT_SOURCE_DIR}/yaner ${CMAKE_SOURCE_DIR}/bin/yaner
    DEPENDS ${CMAKE_BINARY_DIR}/src/yaner
)

ADD_DEFINITIONS(-W -Wall)

# Creates app bundle in /bin, uncomment #-dmg to create a dmg output
IF( APPLE )
    ADD_CUSTOM_COMMAND(
        TARGET yaner
        POST_BUILD
        COMMAND macdeployqt ${CMAKE_CURRENT_BINARY_DIR}/../bin/yaner.app -no-plugins #-dmg
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "Deploying the Qt Framework onto the bundle"
    )
ENDIF( APPLE )

