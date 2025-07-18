# QGIS Python Plugin Project File

TEMPLATE = subdirs

SOURCES = \
    src/__init__.py \
    src/config/__init__.py \
    src/config/orbital.py \
    src/data_retriver/__init__.py \
    src/data_retriver/data_retriver.py \
    src/data_retriver/spacetrack_retriver.py \
    src/orbital_data_processor/__init__.py \
    src/orbital_data_processor/orbital_data_processor.py \
    src/orbital_data_processor/pyorbital_processor.py \
    src/orbital_data_processor/skyfield.py \
    src/Space_trace/__init__.py \
    src/Space_trace/Space_trace.py \
    src/Space_trace/Space_trace_dialog.py \
    src/Space_trace/Space_trace_dialog_class.py \
    src/Space_trace/orbital/__init__.py \
    src/Space_trace/orbital/facade.py \
    src/Space_trace/orbital/handler.py \
    src/Space_trace/orbital/saver.py \
    src/spacetrack_client/__init__.py \
    src/spacetrack_client/spacetrack_client.py \
    src/spacetrack_dialog/__init__.py \
    src/spacetrack_dialog/spacetrack_dialog.py \
    src/spacetrack_dialog/custom_query_dialog.py


RESOURCES = \
    resources.qrc

TRANSLATIONS = \
    i18n/af.ts \
    i18n/SpaceTracePlugin_ru.ts 