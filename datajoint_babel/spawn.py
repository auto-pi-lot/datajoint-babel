"""
Utility functions for spawning all classes from all tables
"""
import pdb

import datajoint as dj
from datajoint.user_tables import TableMeta
from datajoint import DataJointError
import typing
import warnings
if typing.TYPE_CHECKING:
    # from datajoint.user_tables import UserTable
    from datajoint.connection import Connection

def spawn_all_schema(connection:typing.Optional['Connection']=None) -> typing.List[TableMeta]:
    """
    Spawn all schema in a table.

    Requires an active datajoint connection!

    Returns:
        list of schemas
    """

    pre_locals = set(locals())
    schemas = dj.list_schemas(connection)
    for schema in schemas:
        sch = dj.schema(schema)
        try:
            sch.spawn_missing_classes()
        except DataJointError as e:
            warnings.warn(f"Could not spawn classes for schema {schema}, got error:\n{e}\n")

    return [cls for cls in locals().values() if isinstance(cls, TableMeta)]





