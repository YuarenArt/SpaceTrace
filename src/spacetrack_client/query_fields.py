"""SpaceTrack satellite catalogue fields shared by the API and its UI."""

field_types = {
    'INTLDES': 'string', 'NORAD_CAT_ID': 'int', 'OBJECT_TYPE': 'string', 'SATNAME': 'string',
    'COUNTRY': 'string', 'LAUNCH': 'date', 'SITE': 'string', 'DECAY': 'date',
    'PERIOD': 'decimal', 'INCLINATION': 'decimal', 'APOGEE': 'int', 'PERIGEE': 'int',
    'COMMENT': 'string', 'COMMENTCODE': 'int', 'RCSVALUE': 'int', 'RCS_SIZE': 'string',
    'FILE': 'int', 'LAUNCH_YEAR': 'int', 'LAUNCH_NUM': 'int', 'LAUNCH_PIECE': 'string',
    'CURRENT': 'enum', 'OBJECT_NAME': 'string', 'OBJECT_ID': 'string', 'OBJECT_NUMBER': 'int'
}

# Order is used by the dialog's operator selector.
operators_by_type = {
    'int': ('=', '!=', '<', '>'),
    'decimal': ('=', '!=', '<', '>'),
    'date': ('=', '!=', '<', '>', 'IS NULL', 'IS NOT NULL'),
    'string': ('=', '!=', 'LIKE'),
    'enum': ('=', '!='),
}
