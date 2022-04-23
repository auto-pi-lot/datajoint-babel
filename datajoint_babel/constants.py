from typing import Literal

from datajoint import Manual, Lookup, Imported, Computed, Part

DATATYPES = Literal[
    "tinyint",
    "smallint",
    "mediumint",
    "int",
    "enum",
    "date",
    "time",
    "datetime",
    "timestamp",
    "char",
    "varchar",
    "float",
    "double",
    "decimal",
    "blob",
    "tinyblob",
    "mediumblob",
    "longblob",
    "attach",
    "filepath"
]
TIER_MAP = {
    'Manual': Manual,
    'Lookup': Lookup,
    'Imported': Imported,
    'Computed': Computed,
    'Part': Part
}
TIERS = Literal['Manual', 'Lookup', 'Imported', 'Computed']

# class TIERS(Enum):
#     Manual = Manual
#     Lookup = Lookup
#     Imported = Imported
#     Computed = Computed
#     Part = Part